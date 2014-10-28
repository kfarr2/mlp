# MLP

## Introduction

MLP - NOTE: Python 2.6 is no longer supported. This site is now being upgraded to Python 3.3

## Installation

In your working directory

    pyvenv-3.3 .env
    source .env/bin/activate
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
    python3.3 ez_setup.py
    easy_install-3.3 pip
    rm -rf setuptools-*.zip ez_setup.py 
    pip3.3 install -r requirements.txt

Try to download ffmpeg *

    wget http://johnvansickle.com/ffmpeg/releases/ffmpeg-2.4.1-64bit-static.tar.xz
    tar -xJf ffmpeg-2.4.1-64bit-static.tar.xz
    mv ffmpeg-2.4.1-64bit-static/ffmpeg .env/bin
    rm -rf ffmpeg-2.4.1-64bit-static ffmpeg-2.4.1-64bit-static.tar.xz

Install RabbitMQ

    yum install rabbitmq-server
    service rabbitmq-server start
    chkconfig rabbitmq-server on

Install ElasticSearch **

    rpm --import http://packages.elasticsearch.org/GPG-KEY-elasticsearch
    echo "[elasticsearch-1.1]
    name=Elasticsearch repository for 1.1.x packages
    baseurl=http://packages.elasticsearch.org/elasticsearch/1.1/centos
    gpgcheck=1
    gpgkey=http://packages.elasticsearch.org/GPG-KEY-elasticsearch
    enabled=1" | sed -e 's/^[ \t]*//'  > /etc/yum.repos.d/elasticsearch.repo
    yum install elasticsearch
    sudo /sbin/chkconfig --add elasticsearch
    sudo service elasticsearch start

## Database Configuration

Configure the settings files

    cp mlp/settings/local.py.template mlp/settings/local.py
    vi mlp/settings/local.py

Sync the database

    ./manage.py syncdb
    ./manage.py migrate

Rebuild the search index

    ./manage.py rebuild_index

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

If you don't set FULL in your environment, the long FFMPEG test is skipped.

Then visit:

10.0.0.10:8000/htmlcov/index.html

# Notes & Troubleshooting

### FFMPEG

*If the URL doesn't work, it means the listed version is no longer current.
Go to the following url, find the link to the latest version and replace
the version numbers in the previous syntax. 
e.g. if the link says "ffmpeg-2.4.1-64bit-static.tar.xz", the version is 2.4.1.

    http://johnvansickle.com/ffmpeg/

### ElasticSearch

**If you get an error saying "Can't start up: Not enough memory", update your version of java

    yum install java-1.6.0-openjdk

