# MLP

## Installation

In your working directory

    make install
    source .env/bin/activate

## Database Configuration

Sync the database

    ./manage.py syncdb
    ./manage.py migrate

Rebuild the search index

    ./manage.py rebuild_index

Edit variables as needed

    vi variables.py

## Running the server

Run the server with

    make

or

    ./manage.py runserver

Run Celery if you are working with file uploading

    celery -A project_name.celery worker --loglevel=info

## Setup a User

    from mlp.users.models import User

    # create a user
    u = User(first_name='foo', last_name='bar', email='foobar@foo.bar', is_staff=True)
    u.set_password("foo")
    u.save()

## Testing and Coverage

Run all tests with a coverage report

    # export FULL=1
    coverage run ./manage.py test && coverage html

Or

    make coverage

If you don't set FULL in your environment, the long FFMPEG test is skipped.

Then visit:

10.0.0.10:8000/htmlcov/index.html
