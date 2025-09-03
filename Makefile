.PHONY: dev test smoke e2e docker-up docker-down

PORT ?= 8000

dev:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && \
	UVICORN_RELOAD=1 .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

smoke:
	. .venv/bin/activate && python tests/smoke.py

e2e:
	npm i && npx playwright install && npx playwright test

docker-up:
	docker compose up --build

docker-down:
	docker compose down

