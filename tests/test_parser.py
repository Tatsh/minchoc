from django.db.models import Q
import pytest

from minchoc.filteryacc import parser


def test_parser_default_chocolatey_search_filter() -> None:
    res: Q = parser.parse("((((Id ne null) and substringof('cat',tolower(Id))) or "
                          "((Description ne null) and substringof('cat',tolower(Description))))"
                          " or ((Tags ne null) and substringof(' cat ',tolower(Tags)))) "
                          "and IsLatestVersion")
    assert res.children[0].children[0].children[0][0] == 'nuget_id__isnull'
    assert res.children[0].children[0].children[0][1] is False
    assert res.children[0].children[0].children[1][0] == 'nuget_id__icontains'
    assert res.children[0].children[0].children[1][1] == 'cat'
    assert res.children[0].children[1].children[0][0] == 'description__isnull'
    assert res.children[0].children[1].children[0][1] is False
    assert res.children[0].children[1].children[1][0] == 'description__icontains'
    assert res.children[0].children[1].children[1][1] == 'cat'
    assert res.children[0].children[2].children[0][0] == 'tags__name__isnull'
    assert res.children[0].children[2].children[0][1] is False
    assert res.children[0].children[2].children[1][0] == 'tags__name__icontains'
    assert res.children[0].children[2].children[1][1] == ' cat '
    assert res.children[1][0] == 'is_latest_version'
    assert res.children[1][1] is True


def test_parser_bad_eq() -> None:
    with pytest.raises(ValueError):
        parser.parse('Id eq Description')


def test_parser_no_tolower() -> None:
    res: Q = parser.parse("substringof('cat',Id)")
    assert res.children[0][0] == 'nuget_id__contains'
    assert res.children[0][1] == 'cat'
