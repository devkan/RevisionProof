import math

import pytest

from revisionproof.intelligence.queries import (
    build_change_map_query,
    build_memory_count_query,
    build_memory_search_query,
    build_recipe_count_query,
    build_recipe_search_query,
    build_smart_scene_search_query,
    normalize_embedding,
    sql_string,
)


def test_recipe_queries_use_only_the_security_definer_views() -> None:
    count = build_recipe_count_query("revisionproof-demo", "text-embedding-005")
    search = build_recipe_search_query(
        "revisionproof-demo", "text-embedding-005", UNIT_VECTOR, "exact"
    )
    assert "FROM approved_edit_recipe_memory" in count
    assert "FROM approved_edit_recipe_memory" in search
    assert "operations_json" in search
    assert "approved_edit_recipes" not in search


def test_smart_scene_query_is_scoped_to_workspace_search_and_asset() -> None:
    query = build_smart_scene_search_query(
        "revisionproof-demo",
        "01M00000000000000000000001",
        "01M00000000000000000000002",
        UNIT_VECTOR,
    )
    assert "FROM smart_scene_search" in query
    assert "workspace_id = 'revisionproof-demo'" in query
    assert "search_id = '01M00000000000000000000001'" in query
    assert "asset_id = '01M00000000000000000000002'" in query
    assert "expires_at > now()" in query


UNIT_VECTOR = [1.0] + [0.0] * 767


def test_embedding_normalization_preserves_direction_and_unit_length() -> None:
    original = [3.0, 4.0] + [0.0] * 766
    normalized = normalize_embedding(original)
    assert normalized[:2] == [0.6, 0.8]
    assert sum(value * value for value in normalized) == pytest.approx(1)
    assert original[:2] == [3.0, 4.0]


@pytest.mark.parametrize(
    "values",
    [[], [1.0] * 767, [1.0] * 769, [0.0] * 768, [math.inf] * 768, [math.nan] * 768],
)
def test_embedding_rejects_wrong_dimension_nonfinite_and_zero(values) -> None:
    with pytest.raises(ValueError, match="embedding"):
        normalize_embedding(values)


@pytest.mark.parametrize("value", ["", "x" * 201, "new\nline", "null\x00byte", "tab\tbyte"])
def test_query_strings_reject_control_characters_and_unbounded_input(value) -> None:
    with pytest.raises(ValueError, match="invalid query string"):
        sql_string(value)


def test_query_strings_escape_backslashes_and_quotes_without_expanding_scope() -> None:
    assert sql_string("owner's \\ library") == "'owner\\'s \\\\ library'"
    query = build_memory_count_query("workspace' OR 1=1 --", "text-embedding-005")
    assert "workspace_id = 'workspace\\' OR 1=1 --'" in query
    assert "AND embedding_model = 'text-embedding-005'" in query
    assert "uniqExact(memory_id)" in query


@pytest.mark.parametrize("engine", ["exact", "hnsw", "qbit"])
def test_vector_queries_keep_server_owned_scope_and_bounded_sorted_results(engine) -> None:
    query = build_memory_search_query(
        "revisionproof-demo", "text-embedding-005", UNIT_VECTOR, engine
    )
    assert "ORDER BY distance ASC LIMIT 15" in query
    assert "proof_json" not in query
    if engine == "hnsw":
        assert "FROM approved_edit_neighbors(" in query
        assert "workspace='revisionproof-demo'" in query
        assert "model='text-embedding-005'" in query
    else:
        assert "workspace_id = 'revisionproof-demo'" in query
        assert "embedding_model = 'text-embedding-005'" in query
        assert "Array(Float32)" in query
        assert "FROM approved_edit_memory" in query
    if engine == "qbit":
        assert "L2DistanceTransposed(embedding_qbit, reference_vector, 16)" in query
    elif engine == "exact":
        assert "L2Distance(embedding, reference_vector)" in query
    assert ("use_skip_indexes = 0" in query) is (engine != "hnsw")


@pytest.mark.parametrize("engine,precision", [("unknown", 16), ("qbit", 11), ("qbit", 33)])
def test_vector_query_rejects_engine_and_precision_outside_contract(engine, precision) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        build_memory_search_query("revisionproof-demo", "model", UNIT_VECTOR, engine, precision)


@pytest.mark.parametrize("memory_id", ["", "a" * 63, "A" * 64, "x' OR 1=1 --"])
def test_memory_count_rejects_invalid_identity(memory_id) -> None:
    with pytest.raises(ValueError, match="invalid memory id"):
        build_memory_count_query("revisionproof-demo", "model", memory_id)


def test_change_map_query_requires_exact_analysis_and_workspace() -> None:
    query = build_change_map_query(
        "revisionproof-demo", "01J00000000000000000000000", "01J00000000000000000000001"
    )
    assert "workspace_id = 'revisionproof-demo'" in query
    assert "run_id = '01J00000000000000000000000'" in query
    assert "analysis_id = '01J00000000000000000000001'" in query
    assert query.endswith("ORDER BY second LIMIT 600")


@pytest.mark.parametrize("identity", ["", "a" * 26, "I" * 26, "01J00000000000000000000000'--"])
def test_change_map_query_rejects_non_ulids(identity) -> None:
    with pytest.raises(ValueError, match="ULIDs"):
        build_change_map_query("revisionproof-demo", identity, "01J00000000000000000000001")
    with pytest.raises(ValueError, match="ULIDs"):
        build_change_map_query("revisionproof-demo", "01J00000000000000000000000", identity)
