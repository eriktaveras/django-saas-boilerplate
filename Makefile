.PHONY: install run migrate test superuser lint format seed clean

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

run:
	python manage.py runserver 5000

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	python manage.py test

superuser:
	python manage.py createsuperuser

lint:
	ruff check .

format:
	ruff format .

seed:
	python manage.py seed_data

clean:
	find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} +
	find . -type f -name "*.pyc" -not -path "./venv/*" -delete
