"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import logging
import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# 프로덕션(Railway 등) 환경에서 DB 테이블 누락 방지를 위한 자동 마이그레이션
try:
    from django.core.management import call_command
    call_command("migrate", interactive=False, stdout=sys.stdout)
except Exception as e:
    logging.getLogger("config.wsgi").warning(f"WSGI 자동 마이그레이션 실행 중 알림: {e}")
