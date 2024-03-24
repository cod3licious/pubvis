import colorsys
import json
import logging
import os
from glob import glob

import joblib
from sklearn.decomposition import KernelPCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.neighbors import NearestNeighbors
from sqlmodel import Session

from src.db import Item, Similarity, create_db_and_tables, engine

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)


def get_colors(N=100):
    return [colorsys.hsv_to_rgb(x * 1.0 / N, 1.0, 0.8) for x in range(N)]


def _item_data_to_json(item_data):
    item_json = {
        "item_id": item_data["item_id"],
        "title": item_data["title"],
        "pub_year": int(item_data["pub_date"].split("-")[0]),
    }
    if "publisher" in item_data:
        item_json["publisher"] = item_data["publisher"]
    if "authors" in item_data:
        authors = item_data["authors"].split(", ")
        item_json["authors"] = ", ".join(authors[:5])
        if len(authors) > 5:
            item_json["authors"] += " et al."
    return item_json


def setup_db(source="pubmed"):
    """Populate database and create artifacts based on given jsons"""
    # load all jsons
    logging.info("[setup_db]: loading jsons")
    items_data = []
    for json_path in glob(f"raw_texts/{source}/*.json"):
        with open(json_path) as f:
            items_data.append(json.load(f))

    # create tf-idf features from title + description
    logging.info("[setup_db]: creating tf-idf features")
    item_texts = [f"{i['title']}\n{i['description']}" for i in items_data]
    vectorizer = TfidfVectorizer(strip_accents="unicode")
    X = vectorizer.fit_transform(item_texts)

    # create t-sne embedding to get coordinates for visualization
    logging.info("[setup_db]: computing embeddings")
    X_kpca = KernelPCA(n_components=100, kernel="linear").fit_transform(X)
    X_tsne = TSNE(metric="cosine", verbose=0, random_state=42).fit_transform(X_kpca)

    # create search tree for similarity search in app
    logging.info("[setup_db]: identifying nearest neighbors")
    n_neighbors = 51
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    nn.fit(X)
    # additionally save item ids together with tree so we can map the index back to our ids
    nn.item_ids_ = [i["item_id"] for i in items_data]
    # get nearest neighbors for all our items to cache them in the DB
    nn_distances, nn_idx = nn.kneighbors(X)

    # save vectorizer and search tree for endpoint later
    logging.info("[setup_db]: saving artifacts")
    os.makedirs(f"assets/{source}", exist_ok=True)
    joblib.dump(vectorizer, f"assets/{source}/vectorizer.pkl")
    joblib.dump(nn, f"assets/{source}/nn_tree.pkl")

    # save item json for frontend
    logging.info("[setup_db]: saving jsons for frontend")
    os.makedirs(f"assets/{source}", exist_ok=True)
    with open(f"assets/{source}/item_info.json", "w") as f:
        f.write(json.dumps({i["item_id"]: _item_data_to_json(i) for i in items_data}))

    # for colors and coordinates we first need to create a color map based on the keywords
    keywords = sorted({i["keywords"] for i in items_data})
    colorlist = get_colors(len(keywords))
    colordict = {
        cat: f"rgb({255 * colorlist[i][0]}, {255 * colorlist[i][1]}, {255 * colorlist[i][2]})"
        for i, cat in enumerate(sorted(keywords))
    }
    # add embedding coordinates and save (fyi: json doesn't like numpy floats)
    xyc_json = [
        {
            "item_id": idata["item_id"],
            "x": float(X_tsne[i, 0]),
            "y": float(X_tsne[i, 1]),
            "color": colordict.get(idata["keywords"], "rgb(169,169,169)"),
        }
        for i, idata in enumerate(items_data)
    ]
    with open(f"assets/{source}/xyc.json", "w") as f:
        f.write(json.dumps(xyc_json))

    # save items with all additional fields in DB
    logging.info("[setup_db]: create database and add items")
    create_db_and_tables()
    with Session(engine) as session:
        for i, item_data in enumerate(items_data):
            # create item with basic info
            item = Item(**item_data)
            # add similar items
            similar_items = [
                Similarity(item_id1=item.item_id, item_id2=nn.item_ids_[nn_idx[i, j]], simscore=100 * (1 - nn_distances[i, j]))
                for j in range(1, n_neighbors)
            ]
            session.add(item)
            session.add_all(similar_items)
        session.commit()


if __name__ == "__main__":
    from src import SOURCE

    if SOURCE not in ("pubmed", "arxiv"):
        raise RuntimeError(f"Unknown SOURCE: {SOURCE} - use 'pubmed' or 'arxiv' instead.")
    setup_db(SOURCE)
