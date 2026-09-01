# Every target runs through the virtualenv that `install` creates. Calling a
# bare `python` here is why five of these used to fail on a fresh clone: the
# venv existed and nothing ever used it.
VENV := venv
PY := $(VENV)/bin/python

.PHONY: install run migrate test superuser lint format seed clean

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo ""
	@echo "Done. Next: cp .env.example .env && make migrate && make run"

run:
	$(PY) manage.py runserver

migrate:
	$(PY) manage.py makemigrations
	$(PY) manage.py migrate

test:
	$(PY) manage.py test

superuser:
	$(PY) manage.py createsuperuser

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

seed:
	$(PY) manage.py seed_data

clean:
	find . -type d -name __pycache__ -not -path "./$(VENV)/*" -exec rm -rf {} +
	find . -type f -name "*.pyc" -not -path "./$(VENV)/*" -delete
