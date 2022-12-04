#!/usr/bin/env python

import colorsys
import urllib.request
import urllib.error
import urllib.parse
import time
import json
import numpy as np
import feedparser
from datetime import datetime
from random import randint
from flask_script import Command
from bs4 import BeautifulSoup as bs
from sklearn.decomposition import TruncatedSVD
from sklearn.manifold import TSNE

from .nlputils_features import FeatureTransform, features2mat
from .nlputils_dict_utils import invert_dict2
from . import db
from .models import *
from .views import process_item


def get_colors(N=100):
    HSV_tuples = [(x * 1.0 / N, 1., 0.8) for x in range(N)]
    return [colorsys.hsv_to_rgb(*x) for x in HSV_tuples]


class Update_index(Command):

    def run(self):
        """compute article features and update the search index"""
        print("[INFO] Update_index: updating features and search index for all items")
        # first, get all items
        items = Item.query.all()
        # then compute features
        print("[INFO] Update_index: computing features")
        ft = FeatureTransform(identify_bigrams=False)
        docfeats = ft.texts2features({a.item_id: a.text for a in items})
        # the index is an inverted dictionary of all item features
        print("[INFO] Update_index: computing indexes")
        index_dict = invert_dict2(docfeats)
        for i, word in enumerate(index_dict):
            index_object = Index.query.get(word)
            if not index_object:
                index_object = Index(word_key=word)
            index_object.doc_dict = json.dumps(index_dict[word])
            db.session.add(index_object)
            if not i % 500:
                print("[INFO] Update_index: committing indexes: %i / %i" % (i, len(index_dict)))
                db.session.commit()
        print("[INFO] Update_index: final commit.")
        db.session.commit()


class Update_similarities(Command):

    def run(self):
        """update the similarities of the items and their 2D embedding"""
        print("[INFO] Update_similarities: updating the similarities for all items")
        # first, get features for all items
        items = Item.query.all()
        print("[INFO] Update_similarities: computing features")
        ft = FeatureTransform(norm_num=False, renorm='max')
        docfeats = ft.texts2features({a.item_id: a.text for a in items})
        doc_ids = list(docfeats.keys())
        # transform features into matrix
        print("[INFO] Update_similarities: transforming features into matrix")
        X, _ = features2mat(docfeats, doc_ids)
        print("[INFO] Update_similarities: performing LSA - explained variance:", end=' ')
        svd = TruncatedSVD(n_components=min(150, int(0.5*X.shape[1])), n_iter=7, random_state=42)
        X = svd.fit_transform(X)
        print(svd.explained_variance_ratio_.sum())
        print("[INFO] Update_similarities: computing cosine similarity")
        xnorm = np.linalg.norm(X, axis=1)
        X /= xnorm.reshape(X.shape[0], 1)
        S = X.dot(X.T)
        print("[INFO] Update_similarities: embedding with t-SNE")
        e_tsne = TSNE(n_components=2, random_state=7, method='exact', perplexity=15, verbose=1)
        X_embed = e_tsne.fit_transform(X)
        print("[INFO] Update_similarities: update items")
        map_did_idx = {did: i for i, did in enumerate(doc_ids)}
        # get 50 closest items for each (excluding the item itself)
        s_idx = np.fliplr(np.argsort(S))[:, 1:min(51, S.shape[1])]
        # delete all old similarity scores first
        Similarity.query.delete(synchronize_session='fetch')
        db.session.commit()
        for i, item in enumerate(items):
            # get index of this item in matrix
            item_idx = map_did_idx[item.item_id]
            # store similarities to other items
            sims = [Similarity(item_id1=item.item_id, item_id2=doc_ids[j], simscore=S[item_idx, j]) for j in s_idx[item_idx, :]]
            db.session.add_all(sims)
            # update coordinates
            item.x = X_embed[item_idx, 0]
            item.y = X_embed[item_idx, 1]
            db.session.add(item)
            if not i % 250:
                print("[INFO] Update_similarities: committing item updates: %i / %i" % (i, len(items)))
                db.session.commit()
        db.session.commit()


class Fetch_pubmed(Command):

    def run(self):
        """download new articles from PubMed"""
        # base url for all pubmed and related queries
        baseurl = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        for keyword in ['brain cancer', 'breast cancer', 'colorectal cancer', 'kidney cancer', 'leukemia',
                        'lung cancer', 'lymphoma cancer', 'melanoma cancer', 'pancreatic cancer', 'prostate cancer']:
            print("[INFO] Fetch_pubmed: downloading new abstracts from pubmed for keyword: %s" % keyword)
            # get a list of 1000 ids
            pmidquery = baseurl + "esearch.fcgi?" + \
                urllib.parse.urlencode({"db": "pubmed", "term": keyword, "retmax": 1000, "sort": "relevance"})
            # retrieve xml
            urlreq = urllib.request.Request(pmidquery, None, {"User-Agent": "python-pubmed%i" % randint(100, 999)})
            xml = urllib.request.urlopen(urlreq).read()
            soup = bs(xml, "xml")
            # extract list of ids if exist
            if int(soup.find("Count").get_text()):
                idlist = [idbla.get_text() for idbla in soup.find("IdList").find_all("Id")]
            else:
                print("[WARNING] Fetch_pubmed: no pubmed ids for keyword: %s" % keyword)
                continue
            # download the pubmed content for all ids
            for i, article_id in enumerate(idlist):
                item = Item.query.get(article_id)
                if not item:
                    try:
                        # get pubmed summary
                        pmquery = baseurl + "efetch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": article_id, "retmode": "xml"})
                        # retrieve xml
                        urlreq = urllib.request.Request(pmquery, None, {"User-Agent": "python-pmc%i" % randint(100, 999)})
                        xml = urllib.request.urlopen(urlreq).read()
                        soup = bs(xml, "xml")
                        article_details = soup.find("PubmedArticleSet").find("PubmedArticle").find("Article")
                        # extract relevant info
                        article_data = {
                            'item_id': article_id,
                            'keywords': keyword
                        }
                        article_data["title"] = article_details.find("ArticleTitle").get_text().replace('[', '').replace(']', '')
                        article_data["publisher"] = article_details.find("Journal").find("Title").get_text()
                        try:
                            year = article_details.find("ArticleDate").find("Year").get_text()
                            month = article_details.find("ArticleDate").find("Month").get_text()
                            day = article_details.find("ArticleDate").find("Day").get_text()
                        except:
                            year = soup.find("PubmedArticleSet").find("PubmedArticle").find("PubmedData").find("History").find("PubMedPubDate").find("Year").get_text()
                            month = soup.find("PubmedArticleSet").find("PubmedArticle").find("PubmedData").find("History").find("PubMedPubDate").find("Month").get_text()
                            day = soup.find("PubmedArticleSet").find("PubmedArticle").find("PubmedData").find("History").find("PubMedPubDate").find("Day").get_text()
                        article_data["pub_date"] = datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
                        article_data["authors"] = ", ".join(["{} {}".format(a.find("ForeName").get_text(), a.find(
                            "LastName").get_text()) for a in article_details.find("AuthorList").find_all("Author") if a.find("ForeName")])
                        # some have no abstract, but we can't use these anyways
                        article_data["description"] = article_details.find('Abstract').get_text()
                        article_data["item_url"] = "https://www.ncbi.nlm.nih.gov/pubmed/%s" % article_id
                        item_id = process_item(article_data)
                    except Exception as e:
                        # only report the error if we failed somewhere besides the abstract and authors (happens for editorial letters)
                        if len(list(article_data.keys())) < 5:
                            print(f"[ERROR] Fetch_pubmed: Something went wrong downloading article id '{article_id}': {e}; obtained:", end=' ')
                            print(list(article_data.keys()))
                # don't download if it already exist, then maybe just update the keyword
                elif item.keywords and keyword not in item.keywords.split(','):
                    item.keywords += ',' + keyword
                    db.session.commit()
                if not i % 100:
                    print("[INFO] Fetch_pubmed: processed %i articles for keyword %s" % (i, keyword))
        print("[INFO] Fetch_pubmed: done.")


class Fetch_arxiv(Command):

    def run(self):
        """download new articles from arxiv"""
        print("[INFO] Fetch_arxiv: Downloading articles from arxiv.")
        # see: https://arxiv.org/help/api/user-manual#detailed_examples
        # instead of making multiple requests we're just being insane and want all 10000 articles at once ;)
        arxiv_query = 'cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML'
        arxiv_baseurl = 'http://export.arxiv.org/api/query?search_query=%s&sortBy=lastUpdatedDate' % arxiv_query
        start_index, max_index, results_per_iteration = 0, 10000, 1000
        n_articles_added = 0
        for i in range(start_index, max_index, results_per_iteration):
            # get all articles
            arxiv_url = arxiv_baseurl + '&start=%i&max_results=%i' % (i, results_per_iteration)
            urlreq = urllib.request.Request(arxiv_url, None, {"User-Agent": "python-arxiv%i" % randint(100, 999)})
            response = urllib.request.urlopen(urlreq).read()
            parse = feedparser.parse(response)
            if not parse.entries:
                # if the process interrupts, it's probably because arxiv cut us off due to rate limiting
                # try running it again and adjust start_index, i.e. set it to i to continue where you left off
                print("[ERROR] Fetch_arxiv: did not receive any articles (i=%i). Exiting.\n%s" % (i, response))
                return
            # save individual articles in database
            for e in parse.entries:
                # check if article already exists (including the newest version)
                article_id, version = e['id'].split('/abs/')[1].split('v')
                item = Item.query.get(article_id)
                if not item or e['id'] > item.item_url:
                    try:
                        article_data = {'item_id': article_id}
                        article_data['title'] = e['title']
                        article_data['authors'] = ", ".join([a['name'] for a in e['authors']])
                        article_data['description'] = e['summary']
                        article_data['keywords'] = e['arxiv_primary_category']['term']
                        article_data['publisher'] = 'arxiv.org preprint - %s' % e['arxiv_primary_category']['term']
                        article_data['pub_date'] = datetime(e['date_parsed'].tm_year, e['date_parsed'].tm_mon, e['date_parsed'].tm_mday).strftime('%Y-%m-%d')
                        article_data['item_url'] = e['id']
                        item_id = process_item(article_data)
                        n_articles_added += 1
                    except Exception as ex:
                        print(f"[ERROR] Fetch_arxiv: Something went wrong with article id '{article_id}': {ex}")
            print("[INFO] Fetch_arxiv: Processed %i articles." % n_articles_added)
            time.sleep(1)
        print("[INFO] Fetch_arxiv: Fetched %i articles. done." % n_articles_added)


class Create_jsons(Command):

    def run(self):
        """create/update the two json files later used in the frontend"""
        print("[INFO] Create_jsons: creating json files for frontend")
        items = Item.query.all()
        # item_info.json is simply a dict with all the item infos
        with open('src/static/json/item_info.json', 'w') as f:
            f.write(json.dumps({i.item_id: i.to_json() for i in items}))
        # for colors and coordinates we first need to create a color map based on the keywords
        keywords = db.session.query(Item.keywords).distinct().all()
        keywords = [k[0] for k in keywords if not "," in k[0]]
        colorlist = get_colors(len(keywords))
        colordict = {cat: "rgb(%i,%i,%i)" % (255 * colorlist[i][0], 255 * colorlist[i][1], 255 * colorlist[i][2]) for i, cat in enumerate(sorted(keywords))}
        with open('src/static/json/xyc.json', 'w') as f:
            f.write(json.dumps([{
                'item_id': i.item_id,
                'x': i.x,
                'y': i.y,
                'color': colordict[i.keywords] if i.keywords in colordict else 'rgb(169,169,169)'
            } for i in items]))


class Export_data(Command):

    def run(self):
        """create json with text + category export used for offline analysis"""
        print("[INFO] Export_data: creating json files for export")
        items = Item.query.all()
        # item_id: text
        with open('src/static/json/item_texts.json', 'w') as f:
            f.write(json.dumps({i.item_id: i.text for i in items}, indent=2))
        # item_id: keyword (or 'mixed')
        with open('src/static/json/item_keywords.json', 'w') as f:
            f.write(json.dumps({i.item_id: i.keywords if not "," in i.keywords else '## mixed ##' for i in items}, indent=2))
