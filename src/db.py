import datetime
import os

from sqlmodel import Field, Relationship, SQLModel, create_engine


class Rating(SQLModel, table=True):
    user_id: str = Field(primary_key=True, foreign_key="user.user_id")
    item_id: str = Field(primary_key=True, foreign_key="item.item_id")
    rating: float
    timestamp: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    rated_items: list[Rating] = Relationship()


class Similarity(SQLModel, table=True):
    item_id1: str = Field(primary_key=True, foreign_key="item.item_id")
    item_id2: str = Field(primary_key=True, foreign_key="item.item_id")
    simscore: float


class Item(SQLModel, table=True):
    item_id: str = Field(primary_key=True)
    title: str
    description: str
    pub_date: str
    keywords: str
    authors: str | None = None
    publisher: str | None = None
    item_url: str | None = None
    similar_items: list[Similarity] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Similarity.item_id1", "order_by": "Similarity.simscore.desc()"}
    )


SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///src/static/assets/database.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
