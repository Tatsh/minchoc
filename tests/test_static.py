from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from django.test import Client


def test_home(client: Client) -> None:
    response = client.get('/')
    assert response.content == b'{}'
    assert response.get('content-type') == 'application/json'
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_metadata(client: Client) -> None:
    response = client.get('/$metadata')
    assert response.get('content-type') == 'application/xml'
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_metadata_alt(client: Client) -> None:
    response = client.get('/$metadata')
    assert response.get('content-type') == 'application/xml'
    assert response.status_code == HTTPStatus.OK
