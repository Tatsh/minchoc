minchoc
=======

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
