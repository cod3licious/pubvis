import time
import json
import unittest
from datetime import datetime, timedelta
from flask import current_app, url_for
from src import create_app, db
from src.models import *
from src.update_db import Update_index, Update_similarities


class PubvisTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_empty_db(self):
        # query all endpoints without them having any items to return
        # no items yet
        response = self.client.get(url_for('.get_random'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # the article for which we want similar ones doesn't exist
        response = self.client.get(url_for('.get_iteminfo', item_id='666'))
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertFalse(json_response['return'])
        self.assertEqual(len(json_response['error']), 1)
        # error for search query w/o q-parameter
        response = self.client.get(url_for('.keyword_search'))
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertFalse(json_response['return'])
        self.assertEqual(len(json_response['error']), 1)
        # no articles that could be searched for
        response = self.client.get(url_for('.keyword_search', q='keyword'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # similarity search get: no articles that could be searched for
        response = self.client.get(url_for('.similarity_search', q='keyword'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # similarity search post: no articles that could be searched for
        response = self.client.post(url_for('.similarity_search'), content_type='application/json', data=json.dumps({'q': 'keyword'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # no similar items for any item yet - get an error
        response = self.client.get(url_for('.get_similar', item_id='666'))
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertFalse(json_response['return'])
        self.assertEqual(len(json_response['error']), 1)
        # no user that could have rated anything
        response = self.client.get(url_for('.get_ratings', user_id='666'))
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertFalse(json_response['return'])
        self.assertEqual(len(json_response['error']), 1)
        # no recommendations for no users - random 0 articles
        response = self.client.get(url_for('.get_recommendation', user_id='666'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)

    def test_add_to_db(self):
        # add an item
        item1 = {
            'item_id': '123',
            'title': 'Title of Article 1',
            'description': 'Abstract of item 1, this is about the brexit, London, and the UK.',
            'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
            'publisher': 'some journal',
            'authors': 'Me'
        }
        response = self.client.post(url_for('.add_item'), content_type='application/json', data=json.dumps(item1))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(json_response['item_id'], '123')
        # manually get the item from the db and check all fields are correct
        item = Item.query.get('123')
        self.assertEqual(item.publisher, item1['publisher'])
        self.assertEqual(item.title, item1['title'])
        self.assertEqual(item.description, item1['description'])
        self.assertEqual(item.authors, item1['authors'])
        self.assertTrue(item1['title'].lower() in item.text)
        self.assertTrue(datetime.utcnow() - item.pub_date > timedelta(days=100))
        # add a second item
        item2 = {
            'item_id': '666',
            'title': 'Title of Article 2',
            'description': 'Abstract of item 2, this is about the brexit, London, and the UK.',
            'text': '',
            'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
            'publisher': 'another journal',
            'keywords': 'UK'
        }
        response = self.client.post(url_for('.add_item'), content_type='application/json', data=json.dumps(item2))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(json_response['item_id'], '666')
        # add the second item again (i.e. same id), check that the item id is the same but updated; new keyword appended
        item2 = {
            'item_id': '666',
            'title': 'New Title',
            'description': 'Abstract of item 2, this is about the brexit, London, and the UK.',
            'text': '',
            'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
            'publisher': 'another journal',
            'keywords': 'brexit'
        }
        response = self.client.post(url_for('.add_item'), content_type='application/json', data=json.dumps(item2))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(json_response['item_id'], '666')
        item = Item.query.get('666')
        self.assertEqual(item.title, item2['title'])
        self.assertEqual(item.keywords, 'UK,brexit')

    def test_get_random(self):
        # add 3 items with different time stamps
        items = [
            {
                'item_id': '1',
                'title': 'title 1',
                'description': 'Abstract of item 1, this is about the brexit, London, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=100), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '2',
                'title': 'title 2',
                'description': 'Abstract of item 2, this is about the brexit, London, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '3',
                'title': 'title 3',
                'description': 'Abstract of item 3, this is about the brexit, London, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            }]
        for i, item in enumerate(items, 1):
            response = self.client.post(url_for('.add_item'),
                                        content_type='application/json', data=json.dumps(item))
            self.assertEqual(response.status_code, 201)
            json_response = json.loads(response.get_data().decode('utf-8'))
            self.assertTrue(json_response['return'])
            self.assertEqual(json_response['item_id'], str(i))
        # query the random endpoint - get all but the second item, which is older than a year
        response = self.client.get(url_for('.get_random'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        self.assertEqual(sorted([json_response['items'][0]['item_id'], json_response['items'][1]['item_id']]), ['1', '3'])

    def test_keyword_search(self):
        # add 3 items with different titles and descriptions
        items = [
            {
                'item_id': '1',
                'title': 'UK and the brexit',
                'description': 'Abstract of item 1, this is about the brexit, London, and the US.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=100), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '2',
                'title': 'something UK, something',
                'description': 'Abstract of item 2, this is about the brexit, London, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '3',
                'title': 'something completely different',
                'description': 'just a bit of BREXIT here.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            }]
        for i, item in enumerate(items, 1):
            response = self.client.post(url_for('.add_item'),
                                        content_type='application/json', data=json.dumps(item))
            self.assertEqual(response.status_code, 201)
            json_response = json.loads(response.get_data().decode('utf-8'))
            self.assertTrue(json_response['return'])
            self.assertEqual(json_response['item_id'], str(i))
        # search: match in title
        response = self.client.get(url_for('.keyword_search', q='uk'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        self.assertEqual(sorted([json_response['items'][0]['item_id'], json_response['items'][1]['item_id']]), ['1', '2'])
        # search: match and
        response = self.client.get(url_for('.keyword_search', q='uk BREXIT'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        self.assertEqual(sorted([json_response['items'][0]['item_id'], json_response['items'][1]['item_id']]), ['1', '2'])
        # search: match and too much
        response = self.client.get(url_for('.keyword_search', q='London Coffee BREXIT'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # search: no match
        response = self.client.get(url_for('.keyword_search', q='Coffee'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)

    def test_get_similar(self):
        # add 3 items with different texts
        items = [
            {
                'item_id': '1',
                'title': 'some article about london',
                'description': 'we are talking about london here, a city in the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=100), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '2',
                'title': 'about brexit',
                'description': 'this is about brexit happening in the uk',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '3',
                'title': 'financial stuff',
                'description': 'something about finances, a topic big in london.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '4',
                'title': 'asdf asdew egrgsdfg',
                'description': 'adskjw welkjx lkwjflk aldkjew3rlkadfg lakrtjlas4',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            }]
        for i, item in enumerate(items, 1):
            response = self.client.post(url_for('.add_item'),
                                        content_type='application/json', data=json.dumps(item))
            self.assertEqual(response.status_code, 201)
            json_response = json.loads(response.get_data().decode('utf-8'))
            self.assertTrue(json_response['return'])
            self.assertEqual(json_response['item_id'], str(i))
        # without initialized similarities we're not getting any results back
        response = self.client.get(url_for('.get_similar', item_id='1'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # first we need to compute the similarities
        updb = Update_similarities()
        updb.run()
        # get similar items
        response = self.client.get(url_for('.get_similar', item_id='1'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 3)
        # the first item has to be more similar than the second
        self.assertGreaterEqual(json_response['items'][0]['simscore'], json_response['items'][1]['simscore'])
        self.assertAlmostEqual(json_response['items'][-1]['simscore'], 0.)
        simscores1 = {json_response['items'][i]['item_id']: json_response['items'][i]['simscore'] for i in range(2)}
        # simscores have to be symmetric
        response = self.client.get(url_for('.get_similar', item_id='2'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 3)
        self.assertGreaterEqual(json_response['items'][0]['simscore'], json_response['items'][1]['simscore'])
        self.assertAlmostEqual(json_response['items'][-1]['simscore'], 0.)
        simscores2 = {json_response['items'][i]['item_id']: json_response['items'][i]['simscore'] for i in range(2)}
        self.assertEqual(simscores1['2'], simscores2['1'])

    def test_similarity_search(self):
        # add 3 items with different titles and descriptions
        items = [
            {
                'item_id': '1',
                'title': 'UK and the brexit',
                'description': 'Abstract of item 1, this is about the brexit, London, and the US.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=100), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '2',
                'title': 'something UK, something',
                'description': 'Abstract of item 2, this is about the New York, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=5000), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '3',
                'title': 'something completely different',
                'description': 'just a bit of BREXIT here.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            }]
        for i, item in enumerate(items, 1):
            response = self.client.post(url_for('.add_item'),
                                        content_type='application/json', data=json.dumps(item))
            self.assertEqual(response.status_code, 201)
            json_response = json.loads(response.get_data().decode('utf-8'))
            self.assertTrue(json_response['return'])
            self.assertEqual(json_response['item_id'], str(i))
        # first we need to compute the search index
        updb = Update_index()
        updb.run()
        # similarity search get
        response = self.client.get(url_for('.similarity_search', q='uk brexit london coffee'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        search_results_get = json_response['items']
        self.assertEqual(len(search_results_get), 3)
        for i in range(3):
            self.assertEqual(search_results_get[i]['item_id'], str(i+1))
        self.assertGreaterEqual(search_results_get[0]['score'], search_results_get[1]['score'])
        self.assertGreaterEqual(search_results_get[1]['score'], search_results_get[2]['score'])
        # similarity search post: no articles that could be searched for
        response = self.client.post(url_for('.similarity_search'), content_type='application/json', data=json.dumps({'q': 'uk brexit london coffee'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        search_results_post = json_response['items']
        self.assertEqual(len(search_results_post), 3)
        for i in range(3):
            self.assertEqual(search_results_post[i]['item_id'], str(i+1))
        self.assertGreaterEqual(search_results_post[0]['score'], search_results_post[1]['score'])
        self.assertGreaterEqual(search_results_post[1]['score'], search_results_post[2]['score'])
        self.assertEqual(search_results_post, search_results_get)

    def test_user_ratings(self):
        # add 3 items
        items = [
            {
                'item_id': '1',
                'title': 'UK and the brexit',
                'description': 'Abstract of item 1, this is about the brexit, London, and the US.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=100), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '2',
                'title': 'something UK, something',
                'description': 'Abstract of item 2, this is about the New York, and the UK.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=10), '%Y-%m-%d'),
                'publisher': 'another journal'
            },
            {
                'item_id': '3',
                'title': 'something completely different',
                'description': 'just a bit of BREXIT here.',
                'text': '',
                'pub_date': datetime.strftime(datetime.utcnow() - timedelta(days=200), '%Y-%m-%d'),
                'publisher': 'another journal'
            }]
        for i, item in enumerate(items, 1):
            response = self.client.post(url_for('.add_item'),
                                        content_type='application/json', data=json.dumps(item))
            self.assertEqual(response.status_code, 201)
            json_response = json.loads(response.get_data().decode('utf-8'))
            self.assertTrue(json_response['return'])
            self.assertEqual(json_response['item_id'], str(i))
        # for the recommendations we need similarities
        updb = Update_similarities()
        updb.run()
        # random recommendations
        response = self.client.get(url_for('.get_recommendation', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 3)
        # manually create user - no ratings yet
        user = User(user_id='test_user')
        db.session.add(user)
        db.session.commit()
        response = self.client.get(url_for('.get_ratings', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 0)
        # add a rating for item 2
        rating = {
            'item_id': 2,
            'user_id': 'test_user',
            'rating': 0.5
        }
        response = self.client.post(url_for('.add_rating'), content_type='application/json', data=json.dumps(rating))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        # check rating
        response = self.client.get(url_for('.get_ratings', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 1)
        self.assertEqual(json_response['items'][0]['item_id'], '2')
        self.assertEqual(json_response['items'][0]['rating'], 0.5)
        # check recommendations
        response = self.client.get(url_for('.get_recommendation', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        # actually, the scores won't always be perfectly sorted since we randomize the results
        self.assertGreaterEqual(json_response['items'][0]['score'], 0.)
        # add another rating for item 1 with default rating
        rating = {
            'item_id': '1',
            'user_id': 'test_user'
        }
        response = self.client.post(url_for('.add_rating'), content_type='application/json', data=json.dumps(rating))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        # check rating
        response = self.client.get(url_for('.get_ratings', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        # newest rating first
        self.assertEqual(json_response['items'][0]['item_id'], '1')
        self.assertEqual(json_response['items'][0]['rating'], 1.)
        # update rating for item 2 with default rating
        rating = {
            'item_id': '2',
            'user_id': 'test_user'
        }
        response = self.client.post(url_for('.add_rating'), content_type='application/json', data=json.dumps(rating))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        # check rating
        response = self.client.get(url_for('.get_ratings', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 2)
        # newest rating first
        self.assertEqual(json_response['items'][0]['item_id'], '2')
        self.assertEqual(json_response['items'][0]['rating'], 1.)
        # check recommendations
        response = self.client.get(url_for('.get_recommendation', user_id='test_user'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data().decode('utf-8'))
        self.assertTrue(json_response['return'])
        self.assertEqual(len(json_response['items']), 1)
        self.assertEqual(json_response['items'][0]['item_id'], '3')
