from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from minchoc.filteryacc import InvalidTypeForEq, parser
import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db.models import Q
    from django.utils.tree import Node


def test_parser_default_chocolatey_search_filter() -> None:
    res: Q = parser.parse("((((Id ne null) and substringof('cat',tolower(Id))) or "
                          "((Description ne null) and substringof('cat',tolower(Description))))"
                          " or ((Tags ne null) and substringof(' cat ',tolower(Tags)))) "
                          "and IsLatestVersion")
    rc0 = cast('Node', res.children[0])
    rc0c0 = cast('Node', rc0.children[0])
    rc0c0c0 = cast('Sequence[Any]', rc0c0.children[0])
    rc0c0c1 = cast('Sequence[Any]', rc0c0.children[1])
    rc0c1 = cast('Node', rc0.children[1])
    rc0c1c0 = cast('Sequence[Any]', rc0c1.children[0])
    rc0c1c1 = cast('Sequence[Any]', rc0c1.children[1])
    rc0c2 = cast('Node', rc0.children[2])
    rc0c2c0 = cast('Sequence[Any]', rc0c2.children[0])
    rc0c2c1 = cast('Sequence[Any]', rc0c2.children[1])
    rc1 = cast('Sequence[Any]', res.children[1])
    assert rc0c0c0[0] == 'nuget_id__isnull'
    assert rc0c0c0[1] is False
    assert rc0c0c1[0] == 'nuget_id__icontains'
    assert rc0c0c1[1] == 'cat'
    assert rc0c1c0[0] == 'description__isnull'
    assert rc0c1c0[1] is False
    assert rc0c1c1[0] == 'description__icontains'
    assert rc0c1c1[1] == 'cat'
    assert rc0c2c0[0] == 'tags__name__isnull'
    assert rc0c2c0[1] is False
    assert rc0c2c1[0] == 'tags__name__icontains'
    assert rc0c2c1[1] == ' cat '
    assert rc1[0] == 'is_latest_version'
    assert rc1[1] is True


def test_parser_bad_eq() -> None:
    with pytest.raises(InvalidTypeForEq):
        parser.parse('Id eq Description')


def test_parser_no_tolower() -> None:
    res: Q = parser.parse("substringof('cat',Id)")
    rc0 = cast('Sequence[Any]', res.children[0])
    assert rc0[0] == 'nuget_id__contains'
    assert rc0[1] == 'cat'
