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

# 프로덕션 환경 관리자(슈퍼유저) 계정 자동 생성 및 비밀번호 동기화
try:
    from django.contrib.auth.models import User
    admin_user = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    admin_pass = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin1234!")
    admin_email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

    user, created = User.objects.get_or_create(
        username=admin_user,
        defaults={"email": admin_email},
    )
    user.set_password(admin_pass)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    if created:
        print(f"[WSGI] 관리자 계정 '{admin_user}'이(가) 자동 생성되었습니다.")
    else:
        print(f"[WSGI] 관리자 계정 '{admin_user}' 비밀번호 및 권한이 동기화되었습니다.")
except Exception as e:
    logging.getLogger("config.wsgi").warning(f"WSGI 관리자 계정 설정 중 알림: {e}")
