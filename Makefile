.PHONY: run clean test coverage reload

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
