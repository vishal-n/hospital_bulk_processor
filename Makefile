.PHONY: start stop

start:
	docker compose up --build -d

stop:
	docker compose down
