#!/usr/bin/env python

import re
import json
import random
from math import sqrt
from datetime import datetime, timedelta
import requests
from sqlalchemy import and_, or_, func
from flask import jsonify, make_response, abort, url_for, current_app, request, redirect, render_template
from unidecode import unidecode

from .nlputils_features import preprocess_text, norm_whitespace
from .nlputils_dict_utils import combine_dicts
from . import blueprint, db
from .models import *


@blueprint.teardown_request
def teardown_request(exception=None):
    if exception:
        db.session.rollback()
    db.session.remove()


@blueprint.before_request
def setup_request():
    if not current_app.testing:
        # authenticate by using a custom key
        allowed = True
        # try with custom key
        if current_app.config['SECRET_KEY'] == request.args.get('secret_key'):
            allowed = True
        if not allowed:
            abort(403)


@blueprint.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'return': False, 'error': ['Not found']}), 404)


@blueprint.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'return': False, 'error': ['Forbidden']}), 403)


@blueprint.errorhandler(400)
def missing_data(error):
    return make_response(jsonify({'return': False, 'error': ['Missing data']}), 400)


@blueprint.route('/health')
def health():
    return make_response('', 200)


@blueprint.route('/')
def index():
    # show frontend which will handle the rest
    return render_template('index.html')


@blueprint.route('/about')
def show_about():
    # just a boring about page
    return render_template('about.html')


@blueprint.route('/add_item', methods=['POST'])
def add_item():
    """
    add an item to the database

    POST parameters (json):
        - item_id: (str, required)
        - title: (str, required)
        - description: (str, required)
        - text: (str, optional)
        - publisher: (str, optional)
        - authors: (str, optional)
        - pub_date: (str, highly recommended - date in the format '%Y-%m-%d')
        - item_url: (str, optional)
    returns upon success the item id of the newly created item
    """
    try:
        post_data = request.get_json()
    except:
        abort(400)
    item_id = process_item(post_data)
    if item_id:
        return make_response(jsonify({"return": True, "item_id": item_id}), 201)
    abort(400)


def process_item(item_data):
    """
    helper function to do the main work of add_item and can be used by other functions
    """
    try:
        # additionally add the title + description to the text
        text = preprocess_text(f"{item_data['title']}\n{item_data['description']}\n{item_data.get('text', '')}")
        # based on the id, check if the item already exists, else create it
        item = Item.query.get(item_data['item_id'])
        if not item:
            item = Item(item_id=item_data['item_id'])
        elif item.keywords and 'keywords' in item_data and not item_data['keywords'] in item.keywords.split(','):
            # keywords are a special case, if it already has one, append the new one instead of replacing it
            item.keywords += ',' + norm_whitespace(item_data['keywords'])
        item.title = norm_whitespace(item_data['title'])
        item.description = norm_whitespace(item_data['description'])
        item.text = " " + text + " "  # pad with spaces to fix search at the end of the sentence
        if 'publisher' in item_data:
            item.publisher = item_data['publisher']
        if 'pub_date' in item_data:
            item.pub_date = datetime.strptime(item_data['pub_date'], '%Y-%m-%d')
        if 'authors' in item_data:
            item.authors = norm_whitespace(item_data['authors'])
        if 'item_url' in item_data:
            item.item_url = norm_whitespace(item_data['item_url'])
        if 'keywords' in item_data and not item.keywords:
            # if we already have a keyword we shouldn't overwrite it, it was handled from before
            item.keywords = norm_whitespace(item_data['keywords'])
    except Exception as e:
        print(f"[ERROR]: Something went wrong extracting the data for item '{unidecode(item_data['title'])}': {e}")
        return 0
    db.session.add(item)
    db.session.commit()
    return item.item_id


@blueprint.route('/random')
def get_random():
    """
    get some random items from the last year
    """
    n = int(request.args.get('n', 20))
    items = Item.query.filter(Item.pub_date > datetime.utcnow() - timedelta(days=365))
    #items = [item.to_json() for item in items.order_by(func.rand()).limit(n).all()]
    items = [item.to_json(True) for item in items.order_by(Item.pub_date.desc()).limit(n).all()]
    return make_response(jsonify({"return": True, "items": items}), 200)


@blueprint.route('/item/<item_id>')
def get_iteminfo(item_id):
    """
    return infos for requested item
    """
    item = Item.query.get(item_id)
    if item:
        return make_response(jsonify({"return": True, "item": item.to_json(True)}), 200)
    abort(404)


@blueprint.route('/search')
def keyword_search():
    """
    search the items for the provided query (quick keyword search)

    GET Parameters:
        - q: search terms (mandatory!)
        - n: number of items to return (default: 5)
    """
    q = request.args.get('q')
    if not q:
        return make_response(jsonify({"return": False, "error": ["no search query q provided"]}), 400)
    n = int(request.args.get('n', 5))
    # the text should contain all the query words
    q = re.sub(r"[^A-Za-z0-9'-]+", ' ', q.lower())
    # first see if we get matches in the title, else search the whole text
    items = Item.query.filter(Item.title.ilike("%%%s%%" % q)).limit(n).all()
    if not items:
        # maybe they were looking for an author?
        items = Item.query.filter(Item.authors.ilike("%%%s%%" % q)).limit(n).all()
        if not items:
            # filtered by search terms (first try and, never or)
            clauses = [Item.text.ilike(f'% {k} %') for k in preprocess_text(q).split()]
            items = Item.query.filter(and_(*clauses)).limit(n).all()
            # if not items:
            #     items = Item.query.filter(or_(*clauses)).limit(n).all()
    return make_response(jsonify({"return": True, "items": [i.to_json() for i in items]}), 200)


@blueprint.route('/search_similar', methods=['GET', 'POST'])
def similarity_search():
    """
    search the items for the provided query

    GET/POST Parameters:
        - q: search terms (mandatory!)
        - n: number of items to return (default: 20)
    """
    if request.method == 'POST':
        try:
            post_data = request.get_json()
        except:
            abort(400)
        q = post_data.get('q', '')
    else:
        q = request.args.get('q')
    if not q:
        return make_response(jsonify({"return": False, "error": ["no search query q provided"]}), 400)
    n = int(request.args.get('n', 20))
    # not more than 500 words!
    q = set(preprocess_text(q).split()[:500])
    item_scores = {}
    for qterm in q:
        # add up the scores for all docs from the terms given in the query string
        index_obj = Index.query.get(qterm)
        if index_obj:
            item_scores = combine_dicts(item_scores, index_obj.index_dict(), sum)
    # normalize, otherwise, together with the weighting too many are going to be just 0
    # item_scores = norm_dict(item_scores)
    # if ordered by the scores, item_scores gives the documents with the best matches
    sorted_ids = sorted(list(item_scores.keys()), key=item_scores.get, reverse=True)[:n]
    items = []
    norm = sqrt(len(q))
    for aid in sorted_ids:
        if item_scores[aid] > 0.00001:
            idict = Item.query.get(aid).to_json(True)
            idict['score'] = round(100 * item_scores[aid]/norm, 1)
            items.append(idict)
    return make_response(jsonify({"return": True, "items": items}), 200)


@blueprint.route('/similar/<item_id>')
def get_similar(item_id):
    """
    get items similar to this one

    GET Parameters:
        - n: number of items to return (default: 20)
    """
    item = Item.query.get(item_id)
    if not item:
        return make_response(jsonify({"return": False, "error": ["item %s does not exist" % item_id]}), 404)
    n = int(request.args.get('n', 20))
    # get infos from list of similar item ids + scores
    items = []
    for i in item.list_similar_items(n):
        sdict = Item.query.get(i[0]).to_json()
        sdict['simscore'] = round(100 * i[1], 1)
        items.append(sdict)
    return make_response(jsonify({"return": True, "items": items}), 200)


@blueprint.route('/recommendation/<user_id>')
def get_recommendation(user_id):
    """
    get personal item recommendations for the user

    GET Parameters:
        - n: number of items to return (default: 20)
    """
    user = User.query.get(user_id)
    if not user or not user.rated_items.all():
        # send out random items instead
        return get_random()
    n = int(request.args.get('n', 20))
    # get the most similar items for the latest 20 rated items (accumulate similarities with max)
    similarities = {}
    for ra in user.rated_items.filter(Rating.rating > 0).limit(50).all():
        similarities = combine_dicts(similarities, dict(ra.item.list_similar_items(10)))
    # exclude items the user has rated already and items that are older than two year
    similarities = {aid: similarities[aid] for aid in similarities
                    if not user.has_rated(aid) and Item.query.get(aid).pub_date > datetime.utcnow() - timedelta(days=730)}
    items = []
    for aid in sorted(similarities, key=similarities.get, reverse=True)[:5*n]:
        idict = Item.query.get(aid).to_json(True)
        idict['score'] = round(100 * similarities[aid], 1)
        items.append(idict)
    random.shuffle(items)
    return make_response(jsonify({"return": True, "items": items[:n]}), 200)


@blueprint.route('/ratings/<user_id>')
def get_ratings(user_id):
    """
    for a specific user, get a list of all items he has rated
    """
    user = User.query.get(user_id)
    if not user:
        return make_response(jsonify({"return": False, "error": ["user %s not found" % user_id]}), 404)
    if not user.rated_items.all():
        return make_response(jsonify({"return": True, "items": []}), 200)
    items = []
    for ra in user.rated_items.all():
        idict = ra.item.to_json()
        idict['rating'] = ra.rating
        items.append(idict)
    return make_response(jsonify({"return": True, "items": items}), 200)


@blueprint.route('/add_rating', methods=['POST'])
def add_rating():
    """
    update the database to indicate that a user (dis)likes an item

    POST Parameters:
        - user_id: the user that has read the article (str, required)
        - item_id: the article the user has read (str, required)
        - rating: float between -1 and +1 indicating the rating (default: +1)
    """
    try:
        post_data = request.get_json()
    except:
        abort(400)
    user_id = str(post_data.get('user_id', ''))
    item_id = str(post_data.get('item_id', ''))
    rating = float(post_data.get('rating', 1.))
    if not user_id or not item_id:
        return make_response(jsonify({"return": False, "error": ["please send both the user and item ids"]}), 400)
    item = Item.query.get(item_id)
    if not item:
        return make_response(jsonify({"return": False, "error": ["item %s does not exist" % item_id]}), 400)
    user = User.query.get(user_id)
    if not user:
        user = User(user_id=user_id)
        db.session.add(user)
        db.session.commit()
    user.add_rating(item, rating)
    db.session.add(user)
    db.session.add(item)
    db.session.commit()
    return make_response(jsonify({"return": True}), 201)
