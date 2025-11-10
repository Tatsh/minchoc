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

GALLERY_RE = rb'/package/somename/1.0.2</d:Gallery'


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
    response = client.get('/package/fake/123.0.0')
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_put_not_authorized(client: Client) -> None:
    response = client.put('/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_post_not_authorized(client: Client) -> None:
    response = client.put('/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_put_invalid_content_type_unknown(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/package/', headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid content type: unknown'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_invalid_content_type_set(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/package/',
                          'nothing',
                          'application/xml',
                          headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid content type: application/xml'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_no_boundary(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/package/',
                          'nothing',
                          'multipart/form-data',
                          headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.json()['error'] == 'Invalid upload'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_put_no_files(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/package/',
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
    response = client.put('/package/',
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
    response = client.put('/package/',
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


@pytest.mark.django_db(transaction=True)
def test_find_packages_by_id_with_skiptoken(client: Client, nuget_user: NugetUser) -> None:
    """Test $skiptoken parameter in find_packages_by_id view."""
    # Create multiple versions of the same package
    from pathlib import Path
    from tempfile import NamedTemporaryFile
    import zipfile

    versions = ['1.0.0', '1.0.1', '1.0.2', '1.0.3']
    for version in versions:
        with NamedTemporaryFile('rb', prefix='minchoc_test', suffix='.nuget') as tf:
            temp_name = tf.name
        with zipfile.ZipFile(temp_name, 'w') as z:
            z.writestr(
                'test.nuspec', f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd">
  <metadata>
    <id>TestPackage</id>
    <version>{version}</version>
    <title>Test Package</title>
    <authors>Test Author</authors>
    <owners>Test Owner</owners>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectUrl>https://test.example.com</projectUrl>
    <description>Test description</description>
    <summary>Test summary</summary>
    <tags>test</tags>
    <packageSourceUrl>https://test.example.com</packageSourceUrl>
  </metadata>
</package>""")
        content = Path(temp_name).read_bytes()
        content = (b"""--1234abc\r
content-disposition: form-data; name="upload"; filename="test.zip"\r
content-type: application/zip\r
\r
""" + content + b"""\r
--1234abc--""")
        response = client.put(
            '/package/',
            content,
            'multipart/form-data; boundary=1234abc',
            headers={
                'content-length': f'{len(content)}',
                'x-nuget-apikey': nuget_user.token.hex
            },
        )
        assert response.status_code == HTTPStatus.CREATED

    # Test without skiptoken - should return all versions
    response = client.get('/FindPackagesById()?id=TestPackage')
    assert response.status_code == HTTPStatus.OK
    content_s = response.content.decode()
    # Check all versions are present
    for version in versions:
        assert f'<d:Version>{version}</d:Version>' in content_s

    # Test with skiptoken - should skip versions up to and including 1.0.1
    response = client.get("/FindPackagesById()?id=TestPackage&$skiptoken='TestPackage','1.0.1'")
    assert response.status_code == HTTPStatus.OK
    content_s = response.content.decode()
    # Versions 1.0.0 and 1.0.1 should NOT be present
    assert '<d:Version>1.0.0</d:Version>' not in content_s
    assert '<d:Version>1.0.1</d:Version>' not in content_s
    # Versions 1.0.2 and 1.0.3 should be present
    assert '<d:Version>1.0.2</d:Version>' in content_s
    assert '<d:Version>1.0.3</d:Version>' in content_s

    # Test with skiptoken at the end - should return empty or no matching versions
    response = client.get("/FindPackagesById()?id=TestPackage&$skiptoken='TestPackage','1.0.3'")
    assert response.status_code == HTTPStatus.OK
    content_s = response.content.decode()
    # All versions should NOT be present
    for version in versions:
        assert f'<d:Version>{version}</d:Version>' not in content_s


@pytest.mark.django_db(transaction=True)
def test_find_packages_by_id_with_skiptoken_no_packages_found(client: Client) -> None:
    """Test $skiptoken parameter in find_packages_by_id view when no packages are found."""
    response = client.get(
        "/FindPackagesById()?id=NonExistentPackage&$skiptoken='NonExistentPackage','1.0.0'")
    assert response.status_code == HTTPStatus.OK
    content_s = response.content.decode()
    # Since no packages exist, the content should be empty (no entries)
    assert '<entry>' not in content_s


@pytest.mark.django_db
def test_put_too_many_nuspecs_post(client: Client, nuget_user: NugetUser) -> None:
    with NamedTemporaryFile('rb', prefix='minchoc_test', suffix='.zip') as tf:
        temp_name = tf.name
    with zipfile.ZipFile(temp_name, 'w') as z:
        z.writestr('a.nuspec', '')
        z.writestr('b.nuspec', 'aaa')
    content = Path(temp_name).read_bytes()
    content = (b"""--1234abc\r
content-disposition: form-data; name="upload"; filename="a.zip"\r
content-type: application/zip\r
\r
""" + content + b"""\r
--1234abc--""")
    response = client.post('/package/',
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
    content = (b"""--1234abc\r
content-disposition: form-data; name="upload"; filename="a.zip"\r
content-type: application/zip\r
\r
""" + content + b"""\r
--1234abc--""")
    response = client.put('/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })
    assert response.status_code == HTTPStatus.CREATED
    response = client.post('/package/',
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
        '&semVerLevel=2.0.0&$skip=0&$top=1',
    )
    assert re.search(GALLERY_RE, response.content) is not None
    assert response.status_code == HTTPStatus.OK
    # search as performed with ``choco search somename``
    response = client.get(
        '/Packages()',
        QUERY_STRING=("$filter=((((Id ne null) and substringof('somename',tolower(Id))) or "
                      "((Description ne null) and substringof('somename',tolower(Description))))"
                      " or ((Tags ne null) and substringof(' somename ',tolower(Tags)))) "
                      'and IsLatestVersion'))
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
    response = client.get('/package/somename/1.0.2')
    assert response.get('content-type') == 'application/zip'
    assert response.status_code == HTTPStatus.OK
    package = Package._default_manager.filter(nuget_id='somename').first()
    assert package is not None
    assert package.download_count == 1
    response = client.delete('/package/somename/1.0.2')
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    settings.ALLOW_PACKAGE_DELETION = True
    # fetch_package_file DELETE
    response = client.delete('/package/somename/1.0.2')
    assert response.status_code == HTTPStatus.FORBIDDEN
    response = client.delete('/package/somename/1.0.2',
                             headers={'x-nuget-apikey': nuget_user.token.hex})
    assert response.status_code == HTTPStatus.NO_CONTENT
