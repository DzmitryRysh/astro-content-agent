"""Tests for OpenAI Responses API strict-mode schema compliance.

These tests verify that make_strict_schema() produces schemas that satisfy
OpenAI's strict JSON schema requirements:
  - every object has "additionalProperties": false
  - every object lists all its property keys in "required"

The test covers all three payload schemas used with the Responses API:
  - DayPlanPayload      (strategy generation)
  - PostDraftPayload    (post draft generation)
  - ReelDraftPayload    (reel draft generation)
"""

from __future__ import annotations

from typing import Any

import pytest

from astro_content_agent.schemas.drafts import PostDraftPayload, ReelDraftPayload
from astro_content_agent.schemas.strategy import DayPlanPayload
from astro_content_agent.services.ai.responses_runner import _patch_strict, make_strict_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_objects(node: Any, path: str = "") -> list[tuple[str, dict]]:
    """Walk a JSON schema and collect all object-type sub-schemas with their path."""
    results: list[tuple[str, dict]] = []
    if not isinstance(node, dict):
        return results

    is_obj = node.get("type") == "object" or "properties" in node
    if is_obj:
        results.append((path or "<root>", node))

    for name, sub in node.get("$defs", {}).items():
        results.extend(_collect_objects(sub, f"$defs.{name}"))
    for key in ("anyOf", "oneOf", "allOf"):
        for i, sub in enumerate(node.get(key, [])):
            results.extend(_collect_objects(sub, f"{path}.{key}[{i}]"))
    if isinstance(node.get("items"), dict):
        results.extend(_collect_objects(node["items"], f"{path}.items"))
    for prop, sub in node.get("properties", {}).items():
        results.extend(_collect_objects(sub, f"{path}.{prop}"))

    return results


def _assert_strict_objects(schema: dict, label: str) -> None:
    """Assert every object in *schema* satisfies strict-mode constraints."""
    for path, obj in _collect_objects(schema):
        assert obj.get("additionalProperties") is False, (
            f"[{label}] Object at '{path}' missing additionalProperties:false\n"
            f"Schema: {obj}"
        )
        props = obj.get("properties", {})
        required = set(obj.get("required", []))
        missing = set(props.keys()) - required
        assert not missing, (
            f"[{label}] Object at '{path}' has properties not in 'required': {missing}\n"
            f"Schema: {obj}"
        )


# ---------------------------------------------------------------------------
# _patch_strict unit tests
# ---------------------------------------------------------------------------


class TestPatchStrictUnit:
    def test_top_level_object_gets_additional_properties_false(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        _patch_strict(schema)
        assert schema["additionalProperties"] is False

    def test_all_properties_become_required(self):
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],  # notes was optional
        }
        _patch_strict(schema)
        assert set(schema["required"]) == {"title", "notes"}

    def test_nested_defs_patched(self):
        schema = {
            "type": "object",
            "properties": {"item": {"$ref": "#/$defs/Item"}},
            "required": ["item"],
            "$defs": {
                "Item": {
                    "type": "object",
                    "properties": {"val": {"type": "integer"}},
                    "required": ["val"],
                }
            },
        }
        _patch_strict(schema)
        assert schema["$defs"]["Item"]["additionalProperties"] is False

    def test_array_item_objects_patched(self):
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}},
                        "required": ["x"],
                    },
                }
            },
            "required": ["items"],
        }
        _patch_strict(schema)
        items_schema = schema["properties"]["items"]["items"]
        assert items_schema["additionalProperties"] is False

    def test_empty_schema_converted_to_closed_object(self):
        """dict[str, Any] generates {} — must become a closed empty object."""
        node: dict = {}
        _patch_strict(node)
        assert node["type"] == "object"
        assert node["additionalProperties"] is False
        assert node["properties"] == {}
        assert node["required"] == []

    def test_anyof_variants_patched(self):
        schema = {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {"a": {"type": "string"}},
                    "required": ["a"],
                },
                {"type": "null"},
            ]
        }
        _patch_strict(schema)
        assert schema["anyOf"][0]["additionalProperties"] is False

    def test_non_object_schemas_untouched(self):
        schema = {"type": "string"}
        original = dict(schema)
        _patch_strict(schema)
        assert schema == original

    def test_deep_copy_not_mutated_by_make_strict(self):
        """make_strict_schema must not mutate the original schema."""
        original = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
        import copy
        before = copy.deepcopy(original)
        make_strict_schema(original)
        assert original == before  # original unchanged
        assert "additionalProperties" not in original


# ---------------------------------------------------------------------------
# Payload schema strict-mode compliance tests
# ---------------------------------------------------------------------------


class TestDayPlanPayloadStrictSchema:
    def test_schema_passes_strict_constraints(self):
        raw = DayPlanPayload.model_json_schema()
        strict = make_strict_schema(raw)
        _assert_strict_objects(strict, "DayPlanPayload")

    def test_top_level_has_additional_properties_false(self):
        strict = make_strict_schema(DayPlanPayload.model_json_schema())
        assert strict["additionalProperties"] is False

    def test_day_plan_item_def_has_additional_properties_false(self):
        strict = make_strict_schema(DayPlanPayload.model_json_schema())
        item_def = strict["$defs"]["DayPlanItem"]
        assert item_def["additionalProperties"] is False

    def test_all_day_plan_item_properties_required(self):
        strict = make_strict_schema(DayPlanPayload.model_json_schema())
        item_def = strict["$defs"]["DayPlanItem"]
        assert set(item_def["properties"].keys()) == set(item_def["required"])

    def test_notes_required_after_patching(self):
        """notes has a default [] so it's NOT in raw required; strict mode must fix this."""
        raw = DayPlanPayload.model_json_schema()
        assert "notes" not in raw.get("required", [])  # confirm pre-condition
        strict = make_strict_schema(raw)
        assert "notes" in strict["required"]


class TestPostDraftPayloadStrictSchema:
    def test_schema_passes_strict_constraints(self):
        raw = PostDraftPayload.model_json_schema()
        strict = make_strict_schema(raw)
        _assert_strict_objects(strict, "PostDraftPayload")

    def test_top_level_has_additional_properties_false(self):
        strict = make_strict_schema(PostDraftPayload.model_json_schema())
        assert strict["additionalProperties"] is False

    def test_metadata_dict_becomes_closed_object(self):
        """metadata: dict[str, Any] schema should be patched to a closed empty object."""
        strict = make_strict_schema(PostDraftPayload.model_json_schema())
        meta_schema = strict["properties"]["metadata"]
        assert meta_schema.get("type") == "object"
        assert meta_schema.get("additionalProperties") is False

    def test_all_properties_in_required(self):
        strict = make_strict_schema(PostDraftPayload.model_json_schema())
        assert set(strict["properties"].keys()) == set(strict["required"])


class TestReelDraftPayloadStrictSchema:
    def test_schema_passes_strict_constraints(self):
        raw = ReelDraftPayload.model_json_schema()
        strict = make_strict_schema(raw)
        _assert_strict_objects(strict, "ReelDraftPayload")

    def test_top_level_has_additional_properties_false(self):
        strict = make_strict_schema(ReelDraftPayload.model_json_schema())
        assert strict["additionalProperties"] is False

    def test_metadata_dict_becomes_closed_object(self):
        strict = make_strict_schema(ReelDraftPayload.model_json_schema())
        meta_schema = strict["properties"]["metadata"]
        assert meta_schema.get("type") == "object"
        assert meta_schema.get("additionalProperties") is False

    def test_all_properties_in_required(self):
        strict = make_strict_schema(ReelDraftPayload.model_json_schema())
        assert set(strict["properties"].keys()) == set(strict["required"])

    def test_hook_0_3s_present_and_required(self):
        strict = make_strict_schema(ReelDraftPayload.model_json_schema())
        assert "hook_0_3s" in strict["required"]
        assert "hook_0_3s" in strict["properties"]


# ---------------------------------------------------------------------------
# Regression: raw schemas (before patching) would fail strict mode
# ---------------------------------------------------------------------------


class TestRawSchemasWouldFail:
    @pytest.mark.parametrize("schema_cls", [DayPlanPayload, PostDraftPayload, ReelDraftPayload])
    def test_raw_schema_missing_additional_properties(self, schema_cls):
        """Confirm that without patching, schemas lack additionalProperties:false."""
        raw = schema_cls.model_json_schema()
        assert raw.get("additionalProperties") is not False, (
            f"{schema_cls.__name__} raw schema already has additionalProperties:false — "
            "the patch may be redundant."
        )
