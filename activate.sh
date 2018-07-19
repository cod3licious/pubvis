#!/bin/bash 

# otherwise the script will work but you won't end up in the virtualenv
if [ "$0" = "./activate.sh" ]
then
    echo "Please do:"
    echo "source activate.sh"
    exit 1
fi

# Select current version of virtualenv:
VERSION=15.0.1
# Name your first "bootstrap" environment:
INITIAL_ENV=bootstrap
# Options for your first environment:
ENV_OPTS='' #'--no-site-packages --distribute'
# Set to whatever python interpreter you want for your first environment:
PYTHON=/usr/bin/python  # $(which python)  -- anaconda version doesn't word - fuck it
URL_BASE=https://pypi.python.org/packages/source/v/virtualenv
# Name of the environment to create
PYENV="pubvis"

# --- Real work starts here ---

if [ ! -d ".virtualenv/$PYENV" ]
then
    mkdir -p .virtualenv
    cd .virtualenv 
    echo "Downloading $URL_BASE/virtualenv-$VERSION.tar.gz"
    curl -s -LO $URL_BASE/virtualenv-$VERSION.tar.gz
    tar xvzf virtualenv-$VERSION.tar.gz
    # Create the first "bootstrap" environment.
    $PYTHON virtualenv-$VERSION/virtualenv.py $ENV_OPTS $INITIAL_ENV
    # Don't need this anymore.
    rm -rf virtualenv-$VERSION
    # Install virtualenv into the environment.
    $INITIAL_ENV/bin/pip install virtualenv #-$VERSION.tar.gz

    # Create a second environment from the first:
    echo "Creating $PYENV"
    $INITIAL_ENV/bin/virtualenv -p /usr/bin/python2.7 --distribute $PYENV 
    cd ..
fi

# Activate environment
echo "Activating virtualenv '$PYENV'"
source .virtualenv/$PYENV/bin/activate

# if there are problems on the cluster, try
# rm .virtualenv/(bootstrap|Heatmap)/lib/python2.7/no-global-site-packages.txt

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt
