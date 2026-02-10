mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

loaddata:
	python3 manage.py loaddata regions districts

createadmin:
	./manage.py createsuperuser

dumpdata:
	./manage.py dumpdata apps.Category>categories.json

celery:
	celery -A root worker -l INFO

flower:
	celery -A root.celery flower --port=5001

beat:
	celery -A root beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
