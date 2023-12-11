from collections.abc import Iterator
from typing import Any

import pytest


@pytest.fixture()
def nuget_user() -> Iterator[Any]:
    from django.contrib.auth.models import User

    from minchoc.models import NugetUser
    user = User.objects.create()
    assert user is not None
    nuget_user = NugetUser._default_manager.first()
    assert nuget_user is not None
    yield nuget_user
    user.delete()
