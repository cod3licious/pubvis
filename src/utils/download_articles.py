import datetime
import json
import logging
import os
import time
import urllib
from random import randint

import bs4 as bs
import feedparser

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


def download_pubmed(json_dir="raw_texts/pubmed", max_articles=10000):
    """Download new articles from PubMed and save as jsons in a folder"""
    # possibly create directory to save downloaded articles
    os.makedirs(json_dir, exist_ok=True)
    # base url for all pubmed and related queries
    baseurl = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    for keyword in [
        "brain cancer",
        "breast cancer",
        "colorectal cancer",
        "kidney cancer",
        "leukemia",
        "lung cancer",
        "lymphoma cancer",
        "melanoma cancer",
        "pancreatic cancer",
        "prostate cancer",
    ]:
        logging.info(f"[download_pubmed]: downloading new abstracts from pubmed for keyword: {keyword}")

        # get a list of ids
        pmidquery = (
            baseurl
            + "esearch.fcgi?"
            + urllib.parse.urlencode(
                {
                    "db": "pubmed",
                    "term": keyword,
                    "retmax": max_articles // 10,
                    "sort": "relevance",
                }
            )
        )
        # retrieve xml
        urlreq = urllib.request.Request(pmidquery, None, {"User-Agent": f"python-pubmed{randint(100, 999)}"})
        xml = urllib.request.urlopen(urlreq).read()
        soup = bs.BeautifulSoup(xml, features="xml")
        # extract list of ids if exist
        if int(soup.find("Count").get_text()):
            idlist = [idbla.get_text() for idbla in soup.find("IdList").find_all("Id")]
        else:
            logging.warning(f"[download_pubmed]: no pubmed ids for keyword: {keyword}")
            continue

        # download the pubmed content for all ids
        for i, article_id in enumerate(idlist):
            # only download if we have not downloaded the article already
            json_path = os.path.join(json_dir, f"{article_id}.json")
            if not os.path.exists(json_path):
                article_data = {"item_id": article_id, "keywords": keyword}
                try:
                    # get pubmed summary
                    pmquery = (
                        baseurl + "efetch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": article_id, "retmode": "xml"})
                    )
                    # retrieve xml
                    urlreq = urllib.request.Request(
                        pmquery,
                        None,
                        {"User-Agent": f"python-pmc{randint(100, 999)}"},
                    )
                    xml = urllib.request.urlopen(urlreq).read()
                    soup = bs.BeautifulSoup(xml, features="xml")
                    article_details = soup.find("PubmedArticleSet").find("PubmedArticle").find("Article")
                    # extract relevant info
                    article_data["title"] = article_details.find("ArticleTitle").get_text().replace("[", "").replace("]", "")
                    article_data["publisher"] = article_details.find("Journal").find("Title").get_text()
                    try:
                        date = article_details.find("ArticleDate")
                        year = date.find("Year").get_text()
                        month = date.find("Month").get_text()
                        day = date.find("Day").get_text()
                    except Exception:
                        date = (
                            soup.find("PubmedArticleSet")
                            .find("PubmedArticle")
                            .find("PubmedData")
                            .find("History")
                            .find("PubMedPubDate")
                        )
                        year = date.find("Year").get_text()
                        month = date.find("Month").get_text()
                        day = date.find("Day").get_text()
                    article_data["pub_date"] = datetime.datetime(int(year), int(month), int(day), tzinfo=datetime.UTC).strftime(
                        "%Y-%m-%d"
                    )
                    article_data["authors"] = ", ".join(
                        [
                            f"{a.find('ForeName').get_text()} {a.find('LastName').get_text()}"
                            for a in article_details.find("AuthorList").find_all("Author")
                            if a.find("ForeName")
                        ]
                    )
                    # some have no abstract, but we can't use these anyways
                    article_data["description"] = article_details.find("Abstract").get_text()
                    article_data["item_url"] = f"https://www.ncbi.nlm.nih.gov/pubmed/{article_id}"
                    # save all data as a json
                    with open(json_path, "w") as f:
                        json.dump(article_data, f, indent=2)
                except Exception as e:
                    # only report the error if we failed somewhere besides the abstract and authors (happens for editorial letters)
                    if len(list(article_data.keys())) < 5:
                        logging.error(
                            f"[download_pubmed]: Something went wrong downloading article id '{article_id}': {e}; obtained: {list(article_data.keys())}"
                        )

            if not i % 100:
                logging.info(f"[download_pubmed]: processed {i} articles for keyword {keyword}")
    logging.info("[download_pubmed]: done.")


def download_arxiv(json_dir="raw_texts/arxiv", max_articles=10000):
    """Download new articles from arxiv and save as jsons in a folder"""
    # possibly create directory to save downloaded articles
    os.makedirs(json_dir, exist_ok=True)
    logging.info("[download_arxiv]: Downloading articles from arxiv.")
    # see: https://arxiv.org/help/api/user-manual#detailed_examples
    arxiv_query = "cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML"
    arxiv_baseurl = f"http://export.arxiv.org/api/query?search_query={arxiv_query}&sortBy=lastUpdatedDate"
    start_index, max_index, results_per_iteration = 0, max_articles, min(max_articles, 1000)
    n_articles_added = 0
    for i in range(start_index, max_index, results_per_iteration):
        # get all articles
        arxiv_url = arxiv_baseurl + f"&start={i}&max_results={results_per_iteration}"
        urlreq = urllib.request.Request(arxiv_url, None, {"User-Agent": f"python-arxiv{randint(100, 999)}"})
        response = urllib.request.urlopen(urlreq).read()
        parse = feedparser.parse(response)
        if not parse.entries:
            # if the process interrupts, it's probably because arxiv cut us off due to rate limiting
            # try running it again and adjust start_index, i.e. set it to i to continue where you left off
            logging.error(f"[download_arxiv]: did not receive any articles (i={i}). Exiting.\n{response}")
            return
        # save individual articles
        for e in parse.entries:
            article_id, version = e["id"].split("/abs/")[1].split("v")
            # only process if we have not downloaded the article already
            json_path = os.path.join(json_dir, f"{article_id}.json")
            if not os.path.exists(json_path):
                try:
                    article_data = {"item_id": article_id}
                    article_data["title"] = e["title"]
                    article_data["authors"] = ", ".join([a["name"] for a in e["authors"]])
                    article_data["description"] = e["summary"]
                    article_data["keywords"] = e["arxiv_primary_category"]["term"]
                    article_data["publisher"] = f"arxiv.org preprint - {e['arxiv_primary_category']['term']}"
                    article_data["pub_date"] = datetime.datetime(
                        e["date_parsed"].tm_year, e["date_parsed"].tm_mon, e["date_parsed"].tm_mday, tzinfo=datetime.UTC
                    ).strftime("%Y-%m-%d")
                    article_data["item_url"] = e["id"]
                    # save all data as a json
                    with open(json_path, "w") as f:
                        json.dump(article_data, f, indent=2)
                    n_articles_added += 1
                except Exception as ex:
                    logging.error(f"[download_arxiv]: Something went wrong with article id '{article_id}': {ex}")
        logging.info(f"[download_arxiv]: Processed {n_articles_added} articles.")
        time.sleep(1)
    logging.info(f"[download_arxiv]: Fetched {n_articles_added} articles. done.")


if __name__ == "__main__":
    from src.main import LABEL

    if LABEL == "pubmed":
        download_pubmed()
    elif LABEL == "arxiv":
        download_arxiv()
    else:
        raise RuntimeError(f"Unknown LABEL: {LABEL} - use 'pubmed' or 'arxiv' instead.")
