# MLP

## Introduction

MLP

## Installation

In your working directory

    virtualenv --no-site-packages .env
    source .env/bin/activate
    pip install -r requirements.txt

    mv mlp/settings/local.py.template $project_name/settings/local.py
    vi mlp/settings/local.py

Install RabbitMQ if you need it

    yum install rabbitmq-server
    service rabbitmq-server start
    chkconfig rabbitmq-server on

Install ElasticSearch if you need it

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

If you get an error saying "Can't start up: Not enough memory", update your version of java

    yum install java-1.6.0-openjdk

Rebuild the search index

    ./manage.py rebuild_index

Run Celery if you are working with task queues

    celery -A project_name.celery worker --loglevel=info

Sync the database

    ./manage.py syncdb
    ./manage.py migrate

Run the server

    make

or

    ./manage.py runserver

