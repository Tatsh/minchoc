<!-- markdownlint-configure-file {"MD024": { "siblings_only": true } } -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.1/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.2.0] - 2026-04-27

### Added

- Asynchronous `NugetUser.atoken_exists` and `NugetUser.arequest_has_valid_token` methods. The
  synchronous counterparts remain available.

### Changed

- Converted views and helpers to use Django's asynchronous view support.
  - `find_packages_by_id`, `packages`, `packages_with_args`, and `fetch_package_file` are now
    declared with `async def`.
  - The `dispatch`, `put`, and `post` methods on `APIV2PackageView` are now declared with
    `async def`.
  - `make_entry` is now declared with `async def`.
  - `home` and `metadata` remain synchronous.

## [0.1.0]

### Added

- Support for `$skiptoken` format `'PackageName','Version'`.

### Changed

- All paths no longer have a prefix. This should be set by the user of this library in their root
  `urls.py`.

## [0.0.11]

### Added

- Added badges to readme.
- Added `__version__` to `minchoc` module.

### Changed

- Switched to [django-stubs](https://github.com/typeddjango/django-stubs)
- Updated all typing to work with Mypy + django-stubs
  - Pyright (and Pylance in VS Code) errors are ignored.
- Upgraded dependencies.
- Now requires `django@^5.0.0`.
- Make use of [Cruft](https://cruft.github.io/cruft/).
- Updated project cruft.
  - Fixed all issues reported by Ruff since cruft update.
- Synchronised [documentation](https://minchoc.readthedocs.io/en/latest/#minchoc) with the readme.
- Changed documentation theme.

### Removed

- Dropped Python 3.10 support

## [0.0.6]

### Changed

- Upgraded dependencies.
- Added tests, coverage at 95%+.

### Removed

- Removed `WANT_NUGET_HOME` setting.

[unreleased]: https://github.com/Tatsh/pychoco/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Tatsh/minchoc/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Tatsh/minchoc/compare/v0.0.11...v0.1.0
[0.0.11]: https://github.com/Tatsh/minchoc/compare/v0.0.6...v0.0.11
[0.0.6]: https://github.com/Tatsh/minchoc/compare/v0.0.5...v0.0.6
