web: gunicorn fileapp.wsgi --log-file -
worker: celery worker -A fileapp -E -l debug