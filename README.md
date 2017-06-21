## READ ME

This is a short introduction to the PubVis web application. For more details please see the accompanying paper. A demo of the app is running [here](https://pubvis.herokuapp.com/) (with PubMed articles about different cancer types) and [here](https://arxvis.herokuapp.com/) (with arXiv articles about machine learning).

# Quick start
To simply create the PubVis application from the paper, open a terminal and `cd` to this repository (i.e. you should be in the folder where `manage.py` lives). 

Optionally (but recommended), you can activate a virtual environment, which installs all the necessary dependencies (running python 2.7):

    $ source activate.sh

To make sure everything is working, you can run the tests with:

    $ python manage.py test

Then execute the following commands to set up the database, fetch articles from PubMed, generate the search index, compute article similarities, and create the 2D embedding of the data (some of these steps might take more than a few minutes):

    $ python manage.py db init
    $ python manage.py db migrate -m "initial migration"
    $ python manage.py db upgrade
    $ python manage.py fetch_pubmed
    $ python manage.py update_index
    $ python manage.py update_similarities
    $ python manage.py create_jsons

Finally, run the app with

    $ python manage.py runserver

And open your browser at http://127.0.0.1:5000/ to see the results.

# More detailed setup description

This assumes you're in the main directory, i.e. where `manage.py` lives.

### Activate virtual environment
To get the app running *locally*, activate the virtual environment, which installs all the necessary dependencies from `requirements.txt` (running python 2.7):

    $ source activate.sh

### Testing the app
To make sure everything is working, you can run the tests with:

    $ python manage.py test

If you changed something in the code, e.g. added advanced features that require a database server other than sqlite, `TEST_DATABASE_URL` in your .env file must point to a valid such database + user and must be different from `DEV_DATABASE_URL` since testing the app always creates new tables and drops them afterwards (i.e. it would delete all your data otherwise).

### Create DB before starting the app for the first time
Make sure the credentials for the `DEV_DATABASE_URL` variable (or `DATABASE_URL` if running in production mode) in your `.env` file match your local database and the user has sufficient privileges (if not using the default sqlite database).

First create the migrations folder with

    $ python manage.py db init

If you plan to change the database schema, edit the `migrations/env.py` file and add `compare_type=True` in `run_migrations_online()` to trigger migrations even if only the type of a column has changed.

    context.configure(connection=connection,
                      target_metadata=target_metadata,
                      compare_type=True,
                      process_revision_directives=process_revision_directives,
                      **current_app.extensions['migrate'].configure_args)

Create the first migration:

    $ python manage.py db migrate -m "initial migration (or sth else)"
And apply the migrations to the database:

    $ python manage.py db upgrade

Repeat these two steps every time you change something in `models.py` to update the database accordingly.

### Filling the database
You can add new PubMed articles to the database for keywords defined in `src/update_db.py` by running

    $ python manage.py fetch_pubmed

Or alternatively you can add articles from ArXiv (currently configured to download articles about machine learning) by running:

    $ python manage.py fetch_arxiv

For all the functions of the app to work, you should then compute the items' features, the search index, the similarities between the items, as well as the embedding coordinates. Some of these steps will take for than a few minutes but for ~10k articles it's fine to run this on a laptop with about 16gb (or maybe even just 8gb) of RAM. So go ahead and execute:

    $ python manage.py update_index
    $ python manage.py update_similarities

To create the visualization, you need to export some data to json files:

    $ python manage.py create_jsons

### Running the app locally
By default, you're running the app in debug mode, which is fine if you're running the app locally (this can be changed by setting `FLASK_CONFIG` in your `.env` file to `production`).

Before running the server, you should always make sure the database is migrated to the latest version (if you've changed something in `models.py`) by executing

    $ python manage.py db upgrade

Then you can run the server with 
    
    $ python manage.py runserver

And by default see the results at http://127.0.0.1:5000/ .

### Running the app in the cloud
Similarly to the demo versions you can also run the app in the cloud, e.g. using web hosting services such as [heroku](https://www.heroku.com/).
For this you probably want to run the app in `production` mode (on heroku you need to set the config vars accordingly). 

Heroku offers a Postgres database add-on, but the free version only gives you 10k free rows, which is probably not enough. If you use the Postgres database, set `DATABASE_URL` in your `.env` file accordingly and then you can also run all the database updates locally by connecting to the database in the cloud (setting `FLASK_CONFIG=production`). Alternatively, you can also use the sqlite database and just add it to your repository and push it to heroku.

As new papers are published every day you should frequently execute the above steps for fetching new content and updating the similarities etc. while either connecting to your heroku database or adding the items to the sqlite database and then committing and pushing it to heroku.
