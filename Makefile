down:
	docker compose down

up:
	docker compose up -docker

restart:
	docker compose restart

rebuild:
	docker compoose down && docker compose up -d --build