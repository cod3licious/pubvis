
import json
from datetime import datetime
from . import db


class Rating(db.Model):
    # which user has rated which item (when)
    __tablename__ = 'ratings'
    user_id = db.Column(db.String, db.ForeignKey('users.user_id'),
                        primary_key=True)
    item_id = db.Column(db.String, db.ForeignKey('items.item_id'),
                        primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<Rating (%r, %r, %r)>' % (self.user_id, self.item_id, self.rating)


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String, primary_key=True)
    # the items the user has rated
    rated_items = db.relationship('Rating',
                                  foreign_keys=[Rating.user_id],
                                  backref=db.backref('user', lazy='joined'),
                                  lazy='dynamic',
                                  cascade='all, delete-orphan',
                                  order_by='desc(Rating.timestamp)')

    def __repr__(self):
        return '<User %r>' % self.user_id

    def add_rating(self, item, rating):
        # add or update a rating
        r = Rating.query.get((self.user_id, item.item_id))
        if r:
            r.rating = rating
            r.timestamp = datetime.utcnow()
        else:
            r = Rating(user=self, item=item, rating=rating)
        db.session.add(r)

    def has_rated(self, item_id):
        return self.rated_items.filter_by(item_id=item_id).first() is not None


class Similarity(db.Model):
    # similar items for each item
    __tablename__ = 'similarities'
    item_id1 = db.Column(db.String, db.ForeignKey('items.item_id'),
                         primary_key=True)
    item_id2 = db.Column(db.String, db.ForeignKey('items.item_id'),
                         primary_key=True)
    simscore = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<Similarity (%r, %r, %r)>' % (self.item_id1, self.item_id2, self.simscore)


class Item(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.String, primary_key=True)
    title = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    text = db.Column(db.UnicodeText, nullable=False)
    publisher = db.Column(db.Unicode)
    authors = db.Column(db.Unicode)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    keywords = db.Column(db.Unicode)
    item_url = db.Column(db.String)
    # image_url = db.Column(db.String)
    # rating_score = db.Column(db.Float, default=0.0001)
    # the users which have rated the item
    similar_items = db.relationship('Similarity',
                                    foreign_keys=[Similarity.item_id1],
                                    backref=db.backref('item', lazy='joined'),
                                    lazy='dynamic',
                                    cascade='all, delete-orphan',
                                    order_by='desc(Similarity.simscore)')
    # the users which have rated the item
    users = db.relationship('Rating',
                            foreign_keys=[Rating.item_id],
                            backref=db.backref('item', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    # coordinates for visualization
    x = db.Column(db.Float)
    y = db.Column(db.Float)

    def was_rated_by(self, user_id):
        return self.users.filter_by(user_id=user_id).first() is not None

    def __repr__(self):
        return '<Item %s>' % self.item_id

    def to_json(self, full=False):
        # return fields relevant for creating a preview etc.
        item = {
            "item_id": self.item_id,
            "title": self.title,
            "pub_year": self.pub_date.year
        }
        if self.publisher:
            item["publisher"] = self.publisher
        if self.authors:
            item["authors"] = ", ".join(self.authors.split(", ")[:5])
            if len(self.authors.split(", ")) > 5:
                item["authors"] += " et al."
        if full:
            item["description"] = self.description
            item["item_url"] = self.item_url
        return item

    def list_similar_items(self, limit=50):
        return [(i.item_id2, i.simscore) for i in self.similar_items[:limit]]


class Index(db.Model):
    # json encoded inverted doc features
    __tablename__ = 'index'
    word_key = db.Column(db.String, primary_key=True)
    doc_dict = db.Column(db.Text)

    def __repr__(self):
        return '<Index %r>' % self.word_key

    def index_dict(self):
        return json.loads(self.doc_dict)
