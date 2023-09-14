from django.test import Client
import pytest

from minchoc.models import NugetUser


def test_home(client: Client) -> None:
    response = client.get('/')
    assert response.content == b'{}'
    assert response.get('content-type') == 'application/json'
    assert response.status_code == 200


@pytest.mark.django_db
def test_metadata(client: Client) -> None:
    response = client.get('/$metadata')
    assert response.get('content-type') == 'application/xml'
    assert response.status_code == 200


@pytest.mark.django_db
def test_put_not_authorized(client: Client) -> None:
    response = client.put('/api/v2/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_not_authorized(client: Client) -> None:
    response = client.post('/api/v2/package/')
    assert response.json()['error'] == 'Not authorized'
    assert response.status_code == 403


@pytest.mark.django_db
def test_put_invalid_content_type_unknown(client: Client, nuget_user: NugetUser) -> None:
    response = client.put('/api/v2/package/', headers={'x-nuget-apikey':
        nuget_user.token.hex})  # type: ignore[arg-type]
    assert response.json()['error'] == 'Invalid content type: unknown'
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_invalid_content_type_set(client: Client, nuget_user: NugetUser) -> None:
    response = client.put(
        '/api/v2/package/',
        'nothing',
        'application/xml',
        headers={'x-nuget-apikey': nuget_user.token.hex})  # type: ignore[arg-type]
    assert response.json()['error'] == 'Invalid content type: application/xml'
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_no_boundary(client: Client, nuget_user: NugetUser) -> None:
    response = client.put(
        '/api/v2/package/',
        'nothing',
        'multipart/form-data',
        headers={'x-nuget-apikey': nuget_user.token.hex})  # type: ignore[arg-type]
    assert response.json()['error'] == 'Invalid upload'
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_no_files(client: Client, nuget_user: NugetUser) -> None:
    response = client.put(
        '/api/v2/package/',
        'nothing',
        'multipart/form-data; boundary=1234abc',
        headers={'x-nuget-apikey': nuget_user.token.hex})  # type: ignore[arg-type]
    assert response.json()['error'] == 'No files sent'
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_too_many_files(client: Client, nuget_user: NugetUser) -> None:
    content = '''--1234abc
content-disposition: form-data; name="upload"; filename="file1.txt"
content-type: text/plain

Some data
--1234abc
content-disposition: form-data; name="upload1"; filename="file2.txt"
content-type: text/plain

Some data2
--1234abc--'''.replace('\n', '\r\n')
    response = client.put('/api/v2/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })  # type: ignore[arg-type]
    assert response.json()['error'] == 'More than one file sent'
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_not_zip_file(client: Client, nuget_user: NugetUser) -> None:
    content = '''--1234abc
content-disposition: form-data; name="upload"; filename="file1.txt"
content-type: text/plain

Some data
--1234abc--'''.replace('\n', '\r\n')
    response = client.put('/api/v2/package/',
                          content,
                          'multipart/form-data; boundary=1234abc',
                          headers={
                              'content-length': f'{len(content)}',
                              'x-nuget-apikey': nuget_user.token.hex
                          })  # type: ignore[arg-type]
    assert response.json()['error'] == 'Not a zip file'
    assert response.status_code == 400
