from django.http import JsonResponse
from django.db import connection
import redis

from root.settings import CELERY_BROKER_URL


def health(request):
    status = {
        "database": "ok",
        "redis": "ok"
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        status["database"] = "error"

    try:
        r = redis.Redis.from_url(CELERY_BROKER_URL)
        r.ping()
    except Exception:
        status["redis"] = "error"

    overall_status = "ok" if all(v == "ok" for v in status.values()) else "error"

    return JsonResponse({
        "status": overall_status,
        "services": status
    })
