This is a short introduction to the PubVis web application. For more details please see the accompanying paper (submitted to KDD).

# Quickstart
To simply create the PubVis application from the paper, open a terminal and `cd` to this repository (i.e. you should be in the folder where `manage.py` lives). 

Optionally, you can activate a virtual environment, which installs all the necessary dependencies (running python 2.7):

    $ source activate.sh

To make sure everything is working, you can run the tests with:

    $ python manage.py test

Then execute the following commands to set up the database, fetch articles from PubMed, generate the search index, compute article similarities, and create the 2D embedding of the data:

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
To get the app running locally, activate the virtual environment, which installs all the necessary dependencies (running python 2.7):

    $ source activate.sh

### Create DB before starting the app for the first time
First create the migrations folder with

    $ python manage.py db init

If you plan to change the database schema, edit the `migrations'env.py` file and add `compare=True` in `run_migrations_online()` to trigger migrations if the type of a column has changed.

    context.configure(connection=connection,
                      target_metadata=target_metadata,
                      compare_type=True,
                      process_revision_directives=process_revision_directives,
                      **current_app.extensions['migrate'].configure_args)

Create the first migration (do this every time you change something in `models.py`):

    $ python manage.py db migrate -m "initial migration (or sth else)"
Then apply the migrations to the database:

    $ python manage.py db upgrade

### Testing the app
To make sure everything is working, you can run the tests with:

    $ python manage.py test

If you changed something in the code, i.e. added advanced features that require a database server other than sqlite, `TEST_DATABASE_URL` in your .env file must point to a valid database + user and must be different from `DEV_DATABASE_URL` since it always creates new tables in the beginning of the tests and drop them afterwards (i.e. it would delete all your data otherwise).

### Running the app
By default, you're running the app in debug mode. To run it in production mode, set the environment variable `FLASK_CONFIG=production` in your `.env` file inside this directory. Also make sure the credentials for the `DEV_DATABASE_URL` variable in your .env file match your local database and the user has sufficient privileges (if not using the default sqlite database).

Before running the server, you should always make sure the database is migrated to the latest version by executing

    $ python manage.py db upgrade

Then you can run the server with 
    
    $ python manage.py runserver

### Filling the database
You can add new pubmed articles to the database for keywords defined in `src/update_db.py` by running

    $ python manage.py fetch_pubmed

For all the functions to work, you should then compute the items' features, the search index, the similarities between the items, as well as the embedding coordinates by executing

    $ python manage.py update_index
    $ python manage.py update_similarities

To create the visualization, you need to export some data to json files:

    $ python manage.py create_jsons
