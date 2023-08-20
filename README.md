# Minimal Chocolatey-compatible NuGet server in a Django app

See above.

## Installation

```shell
pip install minchoc
```

```python
INSTALLED_APPS = ['minchoc']
ALLOW_PACKAGE_DELETION = False
WANT_NUGET_HOME = False
```
