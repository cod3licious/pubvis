import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.db import Item
from src.main import app, get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_empty_db(client: TestClient):
    # query all endpoints without them having any items to return
    # no item details for items that don't exists
    response = client.get("/items/666")
    assert response.status_code == 404
    json_response = response.json()
    assert json_response["detail"] == "Item not found"

    # no items yet - empty list
    response = client.get("/items/random")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 0

    # error for keyword search w/o q-parameter
    response = client.get("/items/search")
    assert response.status_code == 422
    # no articles that could be searched for
    response = client.get("/items/search?q=keyword")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 0

    # no similar items for any item yet - get an error
    response = client.get("/items/666/similar")
    assert response.status_code == 404
    json_response = response.json()
    assert json_response["detail"] == "Item not found"

    # no recommendations for no users - random 0 articles
    response = client.get("/users/666/recommendations")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 0

    # don't test full similarity search since we would have to mock the vectorizer and nn_tree as well :/
    # body = {
    #     "q": "keyword"
    # }
    # response = client.post("/items/similar", json=body)
    # assert response.status_code == 200
    # json_response = response.json()
    # assert len(json_response) == 0


def test_get_items(session: Session, client: TestClient):
    # add 3 items
    items = [
        Item(
            item_id="1",
            title="title 1",
            keywords="test",
            description="Abstract of item 1, this is about the brexit, London, and the UK.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=100)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
        Item(
            item_id="2",
            title="title 2",
            keywords="test",
            description="Abstract of item 2, this is about the brexit, London, and the UK.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=5000)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
        Item(
            item_id="3",
            title="title 3",
            keywords="test",
            description="Abstract of item 3, this is about the brexit, London, and the UK.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=200)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
    ]
    for item in items:
        session.add(item)
    session.commit()

    # get item details for all added items
    for item in items:
        response = client.get(f"/items/{item.item_id}")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["item_id"] == item.item_id
        assert json_response["title"] == item.title

    # query the random endpoint - get all 3 items
    response = client.get("/items/random")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 3


def test_keyword_search(session: Session, client: TestClient):
    # add 3 items with different titles and authors
    items = [
        Item(
            item_id="1",
            title="UK and the brexit",
            keywords="test",
            authors="author1",
            description="Abstract of item 1, this is about the brexit, London, and the US.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=100)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
        Item(
            item_id="2",
            title="something uk lower case, something",
            keywords="test",
            authors="author1",
            description="Abstract of item 2, this is about the brexit, London, and the UK.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=5000)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
        Item(
            item_id="3",
            title="something completely different",
            keywords="test",
            authors="author1, author2, blablubb",
            description="just a bit of BREXIT here.",
            pub_date=(datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=200)).strftime("%Y-%m-%d"),
            publisher="another journal",
        ),
    ]
    for item in items:
        session.add(item)
    session.commit()

    # search: match in title lower case
    response = client.get("/items/search?q=uk")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert sorted([r["item_id"] for r in json_response]) == ["1", "2"]
    # search: match in title upper case
    response = client.get("/items/search?q=UK")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert sorted([r["item_id"] for r in json_response]) == ["1", "2"]
    # search: match all authors
    response = client.get("/items/search?q=author1")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 3
    assert sorted([r["item_id"] for r in json_response]) == ["1", "2", "3"]
    # search: author only in one of them
    response = client.get("/items/search?q=blablubb")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 1
    assert sorted([r["item_id"] for r in json_response]) == ["3"]
    # search: no match
    response = client.get("/items/search?q=Coffee")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 0
