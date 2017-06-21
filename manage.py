#!/usr/bin/env python
import os
import sys
import re

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = re.split('=', line.strip(), 1)
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from src import create_app, db
from src.models import User, Item, Rating, Similarity
from src.update_db import *
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

application = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(application)
migrate = Migrate(application, db)


def make_shell_context():
    return dict(app=application, db=db, User=User, Item=Item, Rating=Rating, Similarity=Similarity)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server())

# very first time: to create the migrations folder
# $ python manage.py db init
# then or every time after something has changed:
# $ python manage.py db migrate -m "this is happening in the migration"
# then apply the migrations
# $ python manage.py db upgrade


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    # migrate database to latest revision
    upgrade()


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    ret = unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful()
    # it's just the other way around...
    if ret == 1:
        sys.exit(0)
    else:
        sys.exit(1)


manager.add_command("fetch_pubmed", Fetch_pubmed)
manager.add_command("fetch_arxiv", Fetch_arxiv)
manager.add_command("update_index", Update_index)
manager.add_command("update_similarities", Update_similarities)
manager.add_command("create_jsons", Create_jsons)
manager.add_command("export_data", Export_data)

if __name__ == '__main__':
    manager.run()
