from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def nuget_user() -> Iterator[Any]:
    from django.contrib.auth.models import User
    from minchoc.models import NugetUser
    user = User._default_manager.create()
    assert user is not None
    nuget_user = NugetUser._default_manager.first()
    assert nuget_user is not None
    yield nuget_user
    user.delete()
