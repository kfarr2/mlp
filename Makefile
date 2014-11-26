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
	# Database stuff
	mysql -e "CREATE DATABASE IF NOT EXISTS mlp"
	./manage.py migrate

.env:
	$(PYTHON) -m venv .env
	curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python
