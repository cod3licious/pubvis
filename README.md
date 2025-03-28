# READ ME

This is a short introduction to the PubVis web application. For more details please see the accompanying [paper](http://arxiv.org/abs/1706.08094). A demo of the app is running [here](https://pubvis.onrender.com) (with PubMed articles about different cancer types) and [here](https://arxvis.onrender.com) (with arXiv articles about machine learning).

If any of this code was helpful for your research, please consider citing it:

    @article{horn2017pubvis,
      title   = {Interactive Exploration and Discovery of Scientific Publications with PubVis},
      author  = {Horn, Franziska},
      journal = {arXiv preprint arXiv:1706.08094},
      year    = {2017}
    }

If you have any questions please don't hesitate to send me an [email](mailto:cod3licious@gmail.com) and of course if you should find any bugs or want to contribute other improvements, pull requests are very welcome!


## Quick start

1.) Open a terminal in the pubvis repo folder.

2.) Install all required packages (assumes an existing uv installation):
```
uv sync
```

3.) Optional: By default we're working with PubMed articles; if you want to work with arXiv articles instead, set `SOURCE = "arxiv"` in `src/__init__.py`.

4.) Download the articles (either from pubmed or arxiv):
```
uv run python src/utils/download_articles.py
```
This will create a folder `raw_texts/pubmed` inside the pubvis folder in which the downloaded articles are saved as json files (this will take a while).

5.) Create the database and trained models (in `src/static/assets`), and two json files (in `src/static/json`) for the frontend from the downloaded articles:
```
uv run python src/utils/setup.py
```

6.) Install frontend dependencies and build (create dist folder; requires node.js and npm installation):
```
cd fronted
npm i
npm run build
```

7.) Optional: Run tests (requires `frontend/dist/` exists):
```
uv run poe test
```

8.) Run the FastAPI app locally (from the root folder):
```
uv run uvicorn src.main:app --reload
```
Open your browser at http://127.0.0.1:8000/ to see the results.


### Acknowledgements

This project was initially a collaboration with [Dmitry Monin](https://www.linkedin.com/in/dmitry-monin-72624176/), who designed and implemented the original frontend. The frontend of the current version was implemented with the help of [Marcel Lengert](https://www.linkedin.com/in/marcel-lengert/).
