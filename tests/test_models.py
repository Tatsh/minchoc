from __future__ import annotations

from minchoc.models import Company, NugetUser, Package, Tag
import pytest


@pytest.mark.django_db
def test_company_str() -> None:
    company = Company._default_manager.create(name='Company name')
    assert str(company) == 'Company name'


@pytest.mark.django_db
def test_tag_str() -> None:
    tag = Tag._default_manager.create(name='Tag name')
    assert str(tag) == 'Tag name'


@pytest.mark.django_db
def test_package_str(nuget_user: NugetUser) -> None:
    package = Package._default_manager.create(nuget_id='somename',
                                              title='somename',
                                              uploader=nuget_user,
                                              version='123.0',
                                              version0=123,
                                              version1=1,
                                              size=1)
    assert str(package) == 'somename 123.0'


@pytest.mark.django_db
def test_nuget_user_str(nuget_user: NugetUser) -> None:
    nuget_user.base.username = 'fakename'
    assert str(nuget_user) == 'fakename'


@pytest.mark.django_db
def test_only_one_nuget_user_is_created_on_first_save() -> None:
    from django.contrib.auth.models import User
    from minchoc.models import NugetUser
    user = User._default_manager.create()
    assert user is not None
    nuget_user = NugetUser._default_manager.filter(base=user).first()
    assert nuget_user is not None
    user.save()
    nuget_users = NugetUser._default_manager.filter(base=user)
    assert nuget_users[0] == nuget_user
    user.delete()
