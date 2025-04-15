from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
import re
import zipfile

from django.conf import settings
from minchoc.models import NugetUser, Package
import pytest

if TYPE_CHECKING:
    from django.test import Client

GALLERY_RE = br'/package/somename/1.0.2</d:Gallery'


@pytest.mark.django_db
def test_packages_invalid_syntax(client: Client) -> None:
    response = client.get('/Packages()',
                          QUERY_STRING='$filter=(tolower(Id) eq somename) and IsLatestVersion')
    assert response.status_code != HTTPStatus.OK


@pytest.mark.django_db
def test_packages_with_args_not_found(client: Client) -> None:
    response = client.get("/Packages(Id='fake',Version='123.0.0')",
                          QUERY_STRING='$filter=(tolower(Id) eq somename) and IsLatestVersion')
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_fetch_package_file(client: Client) -> None:
    response = client.get('/api/v2/package/fake/123.0.0')
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_put_not_authorized(client: Client) -> None:
    response = client.put('/api/v2/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_post_not_authorized(client: Client) -> None:
    response = client.put('/api/v2/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_put_invalid_content_type_unknown(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/api/v2/package/', headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid content type: unknown'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_invalid_content_type_set(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/api/v2/package/',
                          'nothing',
                          'application/xml',
                          headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid content type: application/xml'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_no_boundary(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/api/v2/package/',
                          'nothing',
                          'multipart/form-data',
                          headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid upload'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_no_files(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/api/v2/package/',
                          'nothing',
                          'multipart/form-data; boundary=1234abc',
                          headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'No files sent'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_too_many_files(client: Client, nuget_user: NugetUser) -> None:
    content = """--1234abc
content-disposition: form-data; name="upload"; filename="file1.txt"
content-type: text/plain

Some data
--1234abc
content-disposition: form-data; name="upload1"; filename="file2.txt"
content-type: text/plain

Some data2
--1234abc--""".replace('\n', '\r\n')
    response = client.put('/api/v2/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })
    assert response.json()['error'] == 'More than one file sent'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_not_zip_file(client: Client, nuget_user: NugetUser) -> None:
    content = """--1234abc
content-disposition: form-data; name="upload"; filename="file1.txt"
content-type: text/plain

Some data
--1234abc--""".replace('\n', '\r\n')
    response = client.put('/api/v2/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })
    assert response.json()['error'] == 'Not a zip file'
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_find_package_invalid_req(client: Client) -> None:
    response = client.get('/FindPackagesById()')
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_too_many_nuspecs_post(client: Client, nuget_user: NugetUser) -> None:
    with NamedTemporaryFile('rb', prefix='minchoc_test', suffix='.zip') as tf:
        temp_name = tf.name
    with zipfile.ZipFile(temp_name, 'w') as z:
        z.writestr('a.nuspec', '')
        z.writestr('b.nuspec', 'aaa')
    content = Path(temp_name).read_bytes()
    content = b"""--1234abc\r
content-disposition: form-data; name="upload"; filename="a.zip"\r
content-type: application/zip\r
\r
""" + content + b"""\r
--1234abc--"""
    response = client.post('/api/v2/package/',
                           content,
                           'multipart/form-data; boundary=1234abc',
                           headers={
                               'content-length': f'{len(content)}',
                               'x-nuget-apikey': nuget_user.token.hex
                           })
    assert (response.json()['error'] ==
            'There should be exactly 1 nuspec file present. 0 or more than 1 were found.')
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db(transaction=True)
def test_put(client: Client, nuget_user: NugetUser) -> None:
    with NamedTemporaryFile('rb', prefix='minchoc_test', suffix='.nuget') as tf:
        temp_name = tf.name
    with zipfile.ZipFile(temp_name, 'w') as z:
        z.writestr(
            'a.nuspec', """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd">
  <metadata>
    <id>somename</id>
    <version>1.0.2</version>
    <title>PACKAGE_NAME (Install)</title>
    <authors>AUTHORS</authors>
    <owners>NUGET_MAKER</owners>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectUrl>https://a-url</projectUrl>
    <description>DESCRIPTION</description>
    <summary>SUMMARY</summary>
    <tags>tag1 tag2</tags>
    <packageSourceUrl>https://a-url-can-be-same-as-project</packageSourceUrl>
  </metadata>
</package>""")
    content = Path(temp_name).read_bytes()
    content = b"""--1234abc\r
content-disposition: form-data; name="upload"; filename="a.zip"\r
content-type: application/zip\r
\r
""" + content + b"""\r
--1234abc--"""
    response = client.put('/api/v2/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })
    assert response.status_code == HTTPStatus.CREATED
    response = client.post('/api/v2/package/',
                           content,
                           'multipart/form-data; boundary=1234abc',
                           headers={
                               'content-length': f'{len(content)}',
                               'x-nuget-apikey': nuget_user.token.hex
                           })
    assert response.json()['error'] == 'Integrity error (has this already been uploaded?)'
    assert response.status_code == HTTPStatus.BAD_REQUEST
    # find_packages_by_id
    response = client.get('/FindPackagesById()?semVerLevel=2.0.0&id=somename')
    assert re.search(GALLERY_RE, response.content) is not None
    assert response.status_code == HTTPStatus.OK
    # packages
    response = client.get(
        '/Packages()',
        QUERY_STRING="$filter=(tolower(Id) eq 'somename') and IsLatestVersion&$orderby=id"
        '&semVerLevel=2.0.0&$skip=0&$top=1')
    assert re.search(GALLERY_RE, response.content) is not None
    assert response.status_code == HTTPStatus.OK
    # search as performed with ``choco search somename``
    response = client.get(
        '/Packages()',
        QUERY_STRING=("$filter=((((Id ne null) and substringof('somename',tolower(Id))) or "
                      "((Description ne null) and substringof('somename',tolower(Description))))"
                      " or ((Tags ne null) and substringof(' somename ',tolower(Tags)))) "
                      "and IsLatestVersion"))
    assert re.search(GALLERY_RE, response.content) is not None
    assert response.status_code == HTTPStatus.OK
    # packages_with_args
    response = client.get("/Packages(Id='somename',Version='1.0.2')")
    assert re.search(GALLERY_RE, response.content) is not None
    assert response.status_code == HTTPStatus.OK
    # fetch_package_file
    package = Package._default_manager.filter(nuget_id='somename').first()
    assert package is not None
    assert package.download_count == 0
    response = client.get('/api/v2/package/somename/1.0.2')
    assert response.get('content-type') == 'application/zip'
    assert response.status_code == HTTPStatus.OK
    package = Package._default_manager.filter(nuget_id='somename').first()
    assert package is not None
    assert package.download_count == 1
    response = client.delete('/api/v2/package/somename/1.0.2')
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    settings.ALLOW_PACKAGE_DELETION = True
    # fetch_package_file DELETE
    response = client.delete('/api/v2/package/somename/1.0.2')
    assert response.status_code == HTTPStatus.FORBIDDEN
    response = client.delete('/api/v2/package/somename/1.0.2',
                             headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.status_code == HTTPStatus.NO_CONTENT
