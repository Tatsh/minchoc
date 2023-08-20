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
