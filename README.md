# minchoc

<!-- WISWA-GENERATED-README:START -->

[![Python versions](https://img.shields.io/pypi/pyversions/minchoc.svg?color=blue&logo=python&logoColor=white)](https://www.python.org/)
[![PyPI - Version](https://img.shields.io/pypi/v/minchoc)](https://pypi.org/project/minchoc/)
[![GitHub tag (with filter)](https://img.shields.io/github/v/tag/Tatsh/minchoc)](https://github.com/Tatsh/minchoc/tags)
[![License](https://img.shields.io/github/license/Tatsh/minchoc)](https://github.com/Tatsh/minchoc/blob/master/LICENSE.txt)
[![GitHub commits since latest release (by SemVer including pre-releases)](https://img.shields.io/github/commits-since/Tatsh/minchoc/v0.1.0/master)](https://github.com/Tatsh/minchoc/compare/v0.1.0...master)
[![CodeQL](https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml)
[![QA](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml)
[![Tests](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Tatsh/minchoc/badge.svg?branch=master)](https://coveralls.io/github/Tatsh/minchoc?branch=master)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-blue?logo=dependabot)](https://github.com/dependabot)
[![Documentation Status](https://readthedocs.org/projects/minchoc/badge/?version=latest)](https://minchoc.readthedocs.org/?badge=latest)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django)](https://djangoproject.com)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![uv](https://img.shields.io/badge/uv-261230?logo=astral)](https://docs.astral.sh/uv/)
[![pytest](https://img.shields.io/badge/pytest-zz?logo=Pytest&labelColor=black&color=black)](https://docs.pytest.org/en/stable/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Downloads](https://static.pepy.tech/badge/minchoc/month)](https://pepy.tech/project/minchoc)
[![Stargazers](https://img.shields.io/github/stars/Tatsh/minchoc?logo=github&style=flat)](https://github.com/Tatsh/minchoc/stargazers)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Prettier](https://img.shields.io/badge/Prettier-black?logo=prettier)](https://prettier.io/)

[![@Tatsh](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpublic.api.bsky.app%2Fxrpc%2Fapp.bsky.actor.getProfile%2F%3Factor=did%3Aplc%3Auq42idtvuccnmtl57nsucz72&query=%24.followersCount&label=Follow+%40Tatsh&logo=bluesky&style=social)](https://bsky.app/profile/Tatsh.bsky.social)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Tatsh-black?logo=buymeacoffee)](https://buymeacoffee.com/Tatsh)
[![Libera.Chat](https://img.shields.io/badge/Libera.Chat-Tatsh-black?logo=liberadotchat)](irc://irc.libera.chat/Tatsh)
[![Mastodon Follow](https://img.shields.io/mastodon/follow/109370961877277568?domain=hostux.social&style=social)](https://hostux.social/@Tatsh)
[![Patreon](https://img.shields.io/badge/Patreon-Tatsh2-F96854?logo=patreon)](https://www.patreon.com/Tatsh2)

<!-- WISWA-GENERATED-README:STOP -->

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
