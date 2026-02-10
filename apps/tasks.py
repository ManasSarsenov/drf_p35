import random
import string

from celery import shared_task
from django.core.cache import cache

from apps.utils import logger


def register_key(phone):
    return f"register:{phone}"


@shared_task
def send_sms_code(phone, msg):
    logger.info(f"📞 {phone}\n{msg}")


@shared_task
def register_sms(phone: str):
    code = random.randint(100000, 999999)
    key = register_key(phone)
    if not cache.get(key):
        cache.set(key, code, 60)

    text = f"Tasdiqlash kodi: {code}"
    send_sms_code.delay(phone, text)


#
# @task
# def send_sms_code(phone, msg):
#     logger.info(f"📞 {phone}\n{msg}")
#
#
# @task
# def register_sms(phone: str):
#     code = random.randint(100000, 999999)
#     key = register_key(phone)
#     if not cache.get(key):
#         cache.set(key, code, 60)
#
#     text = f"Tasdiqlash kodi: {code}"
#     send_sms_code.enqueue(phone, text)


def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
