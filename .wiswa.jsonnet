local utils = import 'utils.libjsonnet';

{
  // Project-specific
  description: 'Minimal Chocolatey-compatible NuGet server in a Django app.',
  keywords: ['chocolatey', 'django', 'windows'],
  project_name: 'minchoc',
  version: '0.1.0',
  citation+: {
    'date-released': '2025-04-15',
  },
  gitignore+: ['/packages/'],
  pyproject+: {
    project+: {
      classifiers+: [
        'Environment :: Web Environment',
        'Intended Audience :: Information Technology',
        'Framework :: Django',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Software Distribution',
      ],
    },
    tool+: {
      coverage+: {
        report+: {
          omit+: ['migrations/*', 'parsetab.py', 'test_django*/*', 'wsgi.py'],
        },
        run+: {
          omit+: ['migrations/*', 'parsetab.py', 'test_django*/*', 'wsgi.py'],
        },
      },
      'django-stubs': {
        django_settings_module: 'minchoc',
        ignore_missing_settings: true,
      },
      mypy+: {
        exclude+: ['^minchoc/parsetab.py$'],
        mypy_path: './.stubs',
        plugins: ['mypy_django_plugin.main'],
      },
      poetry+: {
        dependencies+: {
          defusedxml: utils.latestPypiPackageVersionCaret('defusedxml'),
          django: '>=5.2.11',
          'django-stubs-ext': utils.latestPypiPackageVersionCaret('django-stubs-ext'),
          ply: utils.latestPypiPackageVersionCaret('ply'),
        },
        group+: {
          dev+: {
            dependencies+: {
              'django-stubs': utils.latestPypiPackageVersionCaret('django-stubs'),
            },
          },
          tests+: {
            dependencies+: {
              'pytest-django': utils.latestPypiPackageVersionCaret('pytest-django'),
            },
          },
        },
      },
      ruff+: {
        'extend-exclude'+: ['migrations', 'parsetab.py'],
        lint+: {
          'flake8-self'+: {
            'extend-ignore-names'+: ['_base_manager', '_default_manager', '_meta'],
          },
        },
      },
    },
  },
  copilot+: {
    intro: 'minchoc is a MINimal CHOColatey-compatible server app for Django.',
  },
  shared_ignore+: ['test_django*/'],
}
