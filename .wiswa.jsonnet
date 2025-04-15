local utils = import 'utils.libjsonnet';

(import 'defaults.libjsonnet') + {
  // Project-specific
  description: 'Minimal Chocolatey-compatible NuGet server in a Django app.',
  keywords: ['chocolatey', 'django', 'windows'],
  project_name: 'minchoc',
  version: '0.0.11',
  citation+: {
    'date-released': '2025-04-15',
  },
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
          defusedxml: '^0.7.1',
          django: '^5.2',
          'django-stubs-ext': '^5.1.3',
          ply: '^3.11',
        },
        group+: {
          dev+: {
            dependencies+: { 'django-stubs': '^5.1.3' },
          },
          tests+: {
            dependencies+: {
              'pytest-django': '^4.11.1',
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
  skip+: ['tests/test_main.py', 'tests/test_utils.py', 'macprefs/utils.py'],
  // Common
  authors: [
    {
      'family-names': 'Udvare',
      'given-names': 'Andrew',
      email: 'audvare@gmail.com',
      name: '%s %s' % [self['given-names'], self['family-names']],
    },
    {
      'family-names': 'Javier',
      'given-names': 'Francisco',
      email: 'web@inode64.com',
      name: '%s %s' % [self['given-names'], self['family-names']],
    },
  ],
  local funding_name = '%s2' % std.asciiLower(self.github_username),
  github_username: 'Tatsh',
  github+: {
    funding+: {
      ko_fi: funding_name,
      liberapay: funding_name,
      patreon: funding_name,
    },
  },
}
