# Minimal Chocolatey-compatible NuGet server in a Django app

[![Documentation Status](https://readthedocs.org/projects/minchoc/badge/?version=latest)](https://minchoc.readthedocs.io/en/latest/?badge=latest)
[![QA](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/qa.yml)
[![Tests](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml/badge.svg)](https://github.com/Tatsh/minchoc/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Tatsh/minchoc/badge.svg?branch=master)](https://coveralls.io/github/Tatsh/minchoc?branch=master)
![PyPI - Version](https://img.shields.io/pypi/v/minchoc)
![GitHub tag (with filter)](https://img.shields.io/github/v/tag/Tatsh/minchoc)
![GitHub](https://img.shields.io/github/license/Tatsh/minchoc)
![GitHub commits since latest release (by SemVer including pre-releases)](https://img.shields.io/github/commits-since/Tatsh/minchoc/v0.0.8/master)

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

Add `path('', include('minchoc.urls'))` to your root `urls.py`. Example:

```python
from django.urls import include, path
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('minchoc.urls')),
]
```

A `DELETE` call to `/api/v2/package/<id>/<version>` will be denied even with authentication unless
`ALLOW_PACKAGE_DELETION` is set to `True`.

## Notes

When a user is created, a `NugetUser` is also made. This will contain the API key for pushing.
It can be viewed in admin.

Only `choco install` and `choco push` are supported.

### Add source to Chocolatey

As administrator:

```shell
choco source add -s 'https://your-host/url-prefix'
choco apikey add -s 'https://your-host/url-prefix' -k 'your-key'
```

On non-Windows platforms, you can use my [pychoco](https://github.com/Tatsh/pychoco) package, which
also supports the above commands.
