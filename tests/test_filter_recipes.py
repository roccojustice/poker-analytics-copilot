import pytest
from filter_recipes import assemble_where, build_where_clause


def test_assemble_where_mixed_list():
    items = ["first_raise", ("total_raises", ">=", 2), "heads_up_flop"]
    where_sql, params = assemble_where(items)

    assert where_sql == (
        " AND chps.flg_p_first_raise = true"
        " AND hrt.total_p_raises >= %(total_raises_1)s"
        " AND chs.cnt_players_f = 2"
    ), "string items must resolve to their SQL fragment, tuple items to a bound placeholder"
    assert params == {"total_raises_1": 2}, "param name carries the enumerate index, value is bound not interpolated"


def test_assemble_where_repeated_atomic_gets_distinct_param_names():
    items = [("total_raises", "=", 1), ("total_raises", ">=", 2)]
    where_sql, params = assemble_where(items)

    assert where_sql == (
        " AND hrt.total_p_raises = %(total_raises_0)s"
        " AND hrt.total_p_raises >= %(total_raises_1)s"
    ), "the same atomic used twice must produce position-distinct placeholders"
    assert params == {"total_raises_0": 1, "total_raises_1": 2}, "no param-name collision across positions"


def test_assemble_where_rejects_malformed_item():
    with pytest.raises(ValueError):
        assemble_where([("total_raises", "=")])


def test_build_where_clause_unknown_recipe():
    with pytest.raises(ValueError):
        build_where_clause("not_a_real_recipe")
