"""Configuration for Pytest."""
from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import NoReturn
from uuid import uuid4
import os

from django.conf import settings
import pytest

DJANGO_APP_DIR = Path(f'test_django{uuid4().hex}')

pytest_plugins = ['tests.fixtures']

if os.getenv('_PYTEST_RAISE', '0') != '0':  # pragma no cover

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call: pytest.CallInfo[None]) -> NoReturn:
        assert call.excinfo is not None
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo: pytest.ExceptionInfo[BaseException]) -> NoReturn:
        raise excinfo.value


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if os.environ.get('CI') == 'true':
        return
    rmtree(DJANGO_APP_DIR)


def pytest_configure(config: pytest.Config) -> None:
    rmtree(DJANGO_APP_DIR, ignore_errors=True)
    DJANGO_APP_DIR.mkdir(parents=True)
    with (DJANGO_APP_DIR / 'urls.py').open('w') as f:
        f.write("""from django.contrib import admin
from django.urls import include, path
urlpatterns = [path('', include('minchoc.urls'))]""")
    settings.configure(
        ALLOW_PACKAGE_DELETION=False,
        ALLOWED_HOSTS=[],
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test_db'
        }},
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        INSTALLED_APPS=[
            'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
            'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
            'minchoc'
        ],
        LANGUAGE_CODE='en-us',
        LOGGING={},
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware'
        ],
        ROOT_URLCONF=f'{DJANGO_APP_DIR}.urls',
        SECRET_KEY='not a secure key',
        STATIC_URL='static/',
        TIME_ZONE='UTC',
        USE_I18N=True,
        USE_TZ=True,
        WANT_NUGET_HOME=True)
