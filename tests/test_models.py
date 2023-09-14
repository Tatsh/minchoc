import pytest

from minchoc.models import Company, NugetUser, Package, Tag


@pytest.mark.django_db
def test_company_str() -> None:
    company = Company.objects.create(name='Company name')
    assert str(company) == 'Company name'


@pytest.mark.django_db
def test_tag_str() -> None:
    tag = Tag.objects.create(name='Tag name')
    assert str(tag) == 'Tag name'


@pytest.mark.django_db
def test_package_str(nuget_user: NugetUser) -> None:
    package = Package.objects.create(nuget_id='somename',
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
