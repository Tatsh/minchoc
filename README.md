# minchoc

[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/minchoc/)
[![Python versions](https://img.shields.io/pypi/pyversions/minchoc.svg?color=blue&logo=python&logoColor=white)](https://www.python.org/)
[![PyPI - Version](https://img.shields.io/pypi/v/minchoc)](https://pypi.org/project/minchoc/)
[![GitHub tag (with filter)](https://img.shields.io/github/v/tag/Tatsh/minchoc)](https://github.com/Tatsh/minchoc/tags)
[![License](https://img.shields.io/github/license/Tatsh/minchoc)](https://github.com/Tatsh/minchoc/blob/master/LICENSE.txt)
[![GitHub commits since latest release (by SemVer including pre-releases)](https://img.shields.io/github/commits-since/Tatsh/minchoc/v0.1.0/master)](https://github.com/Tatsh/minchoc/compare/v0.1.0...master)
[![CodeQL](https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml)
[![QA](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml)
[![Tests](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Tatsh/minchoc/badge.svg?branch=master)](https://coveralls.io/github/Tatsh/minchoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/minchoc/badge/?version=latest)](https://minchoc.readthedocs.org/?badge=latest)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=green)](https://www.djangoproject.com/)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pydocstyle](https://img.shields.io/badge/pydocstyle-enabled-AD4CD3)](http://www.pydocstyle.org/en/stable/)
[![pytest](https://img.shields.io/badge/pytest-zz?logo=Pytest&labelColor=black&color=black)](https://docs.pytest.org/en/stable/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Downloads](https://static.pepy.tech/badge/minchoc/month)](https://pepy.tech/project/minchoc)
[![Stargazers](https://img.shields.io/github/stars/Tatsh/minchoc?logo=github&style=flat)](https://github.com/Tatsh/minchoc/stargazers)

[![@Tatsh](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpublic.api.bsky.app%2Fxrpc%2Fapp.bsky.actor.getProfile%2F%3Factor%3Ddid%3Aplc%3Auq42idtvuccnmtl57nsucz72%26query%3D%24.followersCount%26style%3Dsocial%26logo%3Dbluesky%26label%3DFollow%2520%40Tatsh&query=%24.followersCount&style=social&logo=bluesky&label=Follow%20%40Tatsh)](https://bsky.app/profile/Tatsh.bsky.social)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109370961877277568?domain=hostux.social&style=social)](https://hostux.social/@Tatsh)

**Min**imal **Choc**olatey-compatible NuGet server in a Django app.

## Installation

```shell
pip install minchoc
```

In `settings.py`, add `'minchoc'` to `INSTALLED_APPS`. Set `ALLOW_PACKAGE_DELETION` to `True` if you
want to enable this API.

```python
INSTALLED_APPS = ['minchoc']
ALLOW_PACKAGE_DELETION = True
```

A `DELETE` call to `/api/v2/package/<id>/<version>` will be denied even with authentication unless
`ALLOW_PACKAGE_DELETION` is set to `True`.

Add `path('/api/v2/', include('minchoc.urls'))` to your root `urls.py`. Example:

```python
from django.urls import include, path
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v2/', include('minchoc.urls')),
]
```

Run `./manage.py migrate` or similar to install the database schema.

## Notes

When a user is created, a `NugetUser` is also made. This will contain the API key for pushing.
It can be viewed in admin.

### Add your source to Chocolatey

As administrator:

```shell
choco source add -s 'https://your-host/url-prefix'
choco apikey add -s 'https://your-host/url-prefix' -k 'your-key'
```

On non-Windows platforms, you can use my [pychoco](https://github.com/Tatsh/pychoco) package, which
also supports the above commands.

### Supported commands

- `choco install`
- `choco push`
- `choco search`
