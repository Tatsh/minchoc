minchoc
=======

.. only:: html

   .. image:: https://img.shields.io/pypi/pyversions/minchoc.svg?color=blue&logo=python&logoColor=white
      :target: https://www.python.org/
      :alt: Python versions

   .. image:: https://img.shields.io/pypi/v/minchoc
      :target: https://pypi.org/project/minchoc/
      :alt: PyPI Version

   .. image:: https://img.shields.io/github/v/tag/Tatsh/minchoc
      :target: https://github.com/Tatsh/minchoc/tags
      :alt: GitHub tag (with filter)

   .. image:: https://img.shields.io/github/license/Tatsh/minchoc
      :target: https://github.com/Tatsh/minchoc/blob/master/LICENSE.txt
      :alt: License

   .. image:: https://img.shields.io/github/commits-since/Tatsh/minchoc/v0.1.0/master
      :target: https://github.com/Tatsh/minchoc/compare/v0.1.0...master
      :alt: GitHub commits since latest release (by SemVer including pre-releases)

   .. image:: https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml/badge.svg
      :target: https://github.com/Tatsh/minchoc/actions/workflows/codeql.yml
      :alt: CodeQL

   .. image:: https://github.com/Tatsh/minchoc/actions/workflows/qa.yml/badge.svg
      :target: https://github.com/Tatsh/minchoc/actions/workflows/qa.yml
      :alt: QA

   .. image:: https://github.com/Tatsh/minchoc/actions/workflows/tests.yml/badge.svg
      :target: https://github.com/Tatsh/minchoc/actions/workflows/tests.yml
      :alt: Tests

   .. image:: https://coveralls.io/repos/github/Tatsh/minchoc/badge.svg?branch=master
      :target: https://coveralls.io/github/Tatsh/minchoc?branch=master
      :alt: Coverage Status

   .. image:: https://readthedocs.org/projects/minchoc/badge/?version=latest
      :target: https://minchoc.readthedocs.org/?badge=latest
      :alt: Documentation Status

   .. image:: https://img.shields.io/badge/Django-092E20?logo=django&logoColor=green
      :target: https://www.djangoproject.com/
      :alt: Django

   .. image:: https://www.mypy-lang.org/static/mypy_badge.svg
      :target: http://mypy-lang.org/
      :alt: mypy

   .. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
      :target: https://github.com/pre-commit/pre-commit
      :alt: pre-commit

   .. image:: https://img.shields.io/badge/pydocstyle-enabled-AD4CD3
      :target: http://www.pydocstyle.org/en/stable/
      :alt: pydocstyle

   .. image:: https://img.shields.io/badge/pytest-zz?logo=Pytest&labelColor=black&color=black
      :target: https://docs.pytest.org/en/stable/
      :alt: pytest

   .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
      :target: https://github.com/astral-sh/ruff
      :alt: Ruff

   .. image:: https://static.pepy.tech/badge/minchoc/month
      :target: https://pepy.tech/project/minchoc
      :alt: Downloads

   .. image:: https://img.shields.io/github/stars/Tatsh/minchoc?logo=github&style=flat
      :target: https://github.com/Tatsh/minchoc/stargazers
      :alt: Stargazers

   .. image:: https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpublic.api.bsky.app%2Fxrpc%2Fapp.bsky.actor.getProfile%2F%3Factor%3Ddid%3Aplc%3Auq42idtvuccnmtl57nsucz72%26query%3D%24.followersCount%26style%3Dsocial%26logo%3Dbluesky%26label%3DFollow%2520%40Tatsh&query=%24.followersCount&style=social&logo=bluesky&label=Follow%20%40Tatsh
      :target: https://bsky.app/profile/Tatsh.bsky.social
      :alt: Follow @Tatsh

   .. image:: https://img.shields.io/mastodon/follow/109370961877277568?domain=hostux.social&style=social
      :target: https://hostux.social/@Tatsh
      :alt: Mastodon Follow

**Min**\imal **Choc**\olatey-compatible NuGet server in a Django app.

Installation
------------

.. code-block:: shell

  pip install minchoc

In ``settings.py``, add ``'minchoc'`` to ``INSTALLED_APPS``. Set ``ALLOW_PACKAGE_DELETION`` to
``True`` if you want to enable this API.

.. code-block:: python

  INSTALLED_APPS = ['minchoc']
  ALLOW_PACKAGE_DELETION = True

A ``DELETE`` call to ``/api/v2/package/<id>/<version>`` will be denied even with authentication
unless ``ALLOW_PACKAGE_DELETION`` is set to ``True``.

Add :code:`path('', include('minchoc.urls'))` to your root ``urls.py``. Example:

.. code-block:: python

  from django.urls import include, path
  urlpatterns = [
      path('admin/', admin.site.urls),
      path('', include('minchoc.urls')),
  ]

Run ``./manage.py migrate`` or similar to install the database schema.

Notes
-----

When a user is created, a ``NugetUser`` is also made. This will contain the API key for pushing.
It can be viewed in admin.

Add your source to Chocolatey
-----------------------------

As administrator:

.. code-block:: powershell

  choco source add -s 'https://your-host/url-prefix'
  choco apikey add -s 'https://your-host/url-prefix' -k 'your-key'

On non-Windows platforms, you can use my `pychoco`_ package, which
also supports the above commands.

.. _pychoco: https://github.com/Tatsh/pychoco

Supported commands
------------------

- :code:`choco install`
- :code:`choco push`
- :code:`choco search`

Models
------

.. automodule:: minchoc.models
   :members:

Views
-----

.. automodule:: minchoc.views
   :members:

Parsing
-------

.. automodule:: minchoc.filteryacc
   :members:

Utilities
---------

.. automodule:: minchoc.utils
   :members:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
