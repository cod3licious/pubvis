import joblib
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from src import SOURCE
from src.db import Item, Rating, User, engine

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")

VECTORIZER = None
NN_TREE = None


# models for incoming and outgoing data
class ItemViewModel(BaseModel):
    item_id: str
    title: str
    description: str
    pub_date: str
    pub_year: int
    keywords: str
    authors: str | None = None
    publisher: str | None = None
    item_url: str | None = None
    score: float | None = None

    @classmethod
    def from_item(cls, item: Item, score: float | None = None):
        if item.authors:
            authors = item.authors.split(", ")
            item.authors = ", ".join(authors[:5])
            if len(authors) > 5:
                item.authors += " et al."
        return cls(**item.dict(), pub_year=int(item.pub_date.split("-")[0]), score=score)


class RatingRequestBody(BaseModel):
    item_id: str
    user_id: str
    rating: float = 1.0


class SimilaritySearchRequestBody(BaseModel):
    q: str
    n: int = 20


# dependencies
def get_session():
    with Session(engine) as session:
        yield session


def get_vectorizer():
    global VECTORIZER
    if VECTORIZER is None:
        VECTORIZER = joblib.load(f"src/static/assets/{SOURCE}/vectorizer.pkl")
    yield VECTORIZER


def get_nn_tree():
    global NN_TREE
    if NN_TREE is None:
        NN_TREE = joblib.load(f"src/static/assets/{SOURCE}/nn_tree.pkl")
    yield NN_TREE


@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse("src/static/html/index.html")


@app.get("/about", include_in_schema=False)
async def read_about():
    return FileResponse("src/static/html/about.html")


@app.get("/health", include_in_schema=False)
def get_health():
    return "alive"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("src/static/favicon.ico")


@app.get("/static_json_item_info", include_in_schema=False)
async def precomputed_item_info_json():
    return FileResponse(f"src/static/json/{SOURCE}/item_info.json")


@app.get("/static_json_xyc", include_in_schema=False)
async def precomputed_xyc_json():
    return FileResponse(f"src/static/json/{SOURCE}/xyc.json")


@app.get("/items/random", response_model=list[ItemViewModel])
def get_random(n: int = 20, session: Session = Depends(get_session)):
    """
    Get a random selection of items

    GET Parameters:
        - n: number of items to return (default: 20)
    """
    items = session.exec(select(Item).order_by(func.random()).limit(n)).all()
    return [ItemViewModel.from_item(item) for item in items]


@app.get("/items/search", response_model=list[ItemViewModel])
def keyword_search(q: str, n: int = 5, session: Session = Depends(get_session)):
    """
    Quick keyword search on title and authors of items

    GET Parameters:
        - q: search terms (mandatory!)
        - n: number of items to return (default: 5)
    """
    items = session.exec(
        select(Item)
        .where(or_(col(Item.title).contains(q), col(Item.authors).contains(q)))
        .order_by(Item.pub_date.desc())
        .limit(n)
    ).all()
    return [ItemViewModel.from_item(item) for item in items]


@app.post("/items/similar", response_model=list[ItemViewModel])
def similarity_search(
    search_body: SimilaritySearchRequestBody,
    session: Session = Depends(get_session),
    vectorizer=Depends(get_vectorizer),
    nn_tree=Depends(get_nn_tree),
):
    """
    Retrieve similar items based on a fulltext search (using the nearest neighbors search tree)

    POST Parameters:
        - q: item full text for search (mandatory!)
        - n: number of items to return (default: 20)
    """
    X = vectorizer.transform([search_body.q])
    nn_distances, nn_idx = nn_tree.kneighbors(X)
    return [
        ItemViewModel.from_item(session.get(Item, nn_tree.item_ids_[j]), 100 * (1 - nn_distances[0, i]))
        for i, j in enumerate(nn_idx[0, : search_body.n])
    ]


@app.get("/items/{item_id}", response_model=ItemViewModel)
def get_item_details(item_id: str, session: Session = Depends(get_session)):
    """
    Get details for a given item
    """
    # NOTE: ordering of functions matters - this needs to come after the other /items/random etc endpoints
    # otherwise they are not found as item_id is a string and therefore also catches random/search/etc!
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemViewModel.from_item(item)


@app.get("/items/{item_id}/similar", response_model=list[ItemViewModel])
def get_similar(item_id: str, n: int = 20, session: Session = Depends(get_session)):
    """
    Get items similar to this one

    GET Parameters:
        - n: number of items to return (default: 20)
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return [ItemViewModel.from_item(session.get(Item, r.item_id2), r.simscore) for r in item.similar_items]


@app.get("/users/{user_id}/recommendations", response_model=list[ItemViewModel])
def get_recommendations(user_id: str, n: int = 20, session: Session = Depends(get_session)):
    """
    Get personal item recommendations for the user;
    returns random items if user has not rated any items yet

    GET Parameters:
        - n: number of items to return (default: 20)
    """
    user = session.get(User, user_id)
    if not user or not user.rated_items:
        return get_random(n, session)

    # retrieve the (positively) rated items for the given user
    rated_items_all = {r.item_id for r in user.rated_items}
    rated_items = {r.item_id for r in user.rated_items if r.rating > 0}
    # extract all the similar items for the rated items and combine their similarity scores by taking the max
    # but exclude items the user has previously rated
    similar_items_dict: dict[str, float] = {}
    for item_id in rated_items:
        item = session.get(Item, item_id)
        for s in item.similar_items:
            if s.item_id2 not in rated_items_all:
                similar_items_dict[s.item_id2] = max(similar_items_dict.get(s.item_id2, 0), s.simscore)
    # limit results to n
    similar_item_ids = sorted(similar_items_dict, key=similar_items_dict.get, reverse=True)[:n]
    similar_items = [
        ItemViewModel.from_item(session.get(Item, item_id), similar_items_dict[item_id]) for item_id in similar_item_ids
    ]

    # return random items if there are no similar items for any reasons (e.g., no positive ratings)
    if not similar_items:
        return get_random(n, session)
    return similar_items


@app.post("/ratings")
def add_rating(rating_body: RatingRequestBody, session: Session = Depends(get_session)):
    """
    Create or update the rating for an item for a user

    POST Parameters:
        - user_id: the user that has read the article
        - item_id: the article the user has read
        - rating: float between -1 and +1 indicating the rating (default: 1)
    """
    item = session.get(Item, rating_body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    user = session.get(User, rating_body.user_id)
    if not user:
        user = User(user_id=rating_body.user_id)
        session.add(user)

    rating = session.get(Rating, (rating_body.user_id, rating_body.item_id))
    if not rating:
        rating = Rating(user_id=rating_body.user_id, item_id=rating_body.item_id, rating=rating_body.rating)
    else:
        rating.rating = rating_body.rating
    session.add(rating)

    session.commit()
