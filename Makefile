.PHONY: run clean test coverage reload install

PYTHON=python3
export PATH:=.env/bin:$(PATH)

# run the django web server
run:
	./manage.py runserver 0.0.0.0:8000

# remove pyc junk
clean:
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete

# run the unit tests
# use `make test test=path.to.test` if you want to run a specific test
test:
	./manage.py test $(test)

# run the unit tests using coverage
coverage:
	coverage run ./manage.py test && coverage html

reload:
	./manage.py migrate && ./manage.py collectstatic --noinput && touch mlp/wsgi.py

# install the site
install: .env

	# Install ffmpeg from CDN
    mkdir bin
    wget https://cdn.research.pdx.edu/ffmpeg/2.4.3/ffmpeg
    mv ffmpeg bin

	# Install requirements
	pip install -r requirements.txt

	# Install RabbitMQ
    yum install rabbitmq-server
    service rabbitmq-server start
    chkconfig rabbitmq-server on

	# Install elasticsearch
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


	mysql -e "CREATE DATABASE IF NOT EXISTS mlp"
	./manage.py migrate
	./manage.py loaddata choices

.env:
	$(PYTHON) -m venv .env
	source .env/bin/activate
	curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python
