"""Tests for Pydantic model validation."""
import pytest
from pydantic import ValidationError

from qsynth.models import (
    Attribute,
    AttributeParams,
    Model,
    RowSpec,
    Schema,
)


def test_attribute_parses_basic():
    """Test basic attribute parsing."""
    attr = Attribute(name="id", type="random_int")
    assert attr.name == "id"
    assert attr.type == "random_int"
    assert attr.params is None


def test_attribute_with_params():
    """Test attribute with parameters."""
    attr = Attribute(
        name="id",
        type="random_int",
        params={"min": 1, "max": 100}
    )
    assert attr.params.min == 1
    assert attr.params.max == 100


def test_attribute_ref_params():
    """Test ${ref} attribute with required params."""
    attr = Attribute(
        name="parent_id",
        type="${ref}",
        params={"dataset": "users", "attribute": "id"}
    )
    assert attr.params.dataset == "users"
    assert attr.params.attribute == "id"


def test_rowspec_validation():
    """Test RowSpec validates min/max."""
    spec = RowSpec(min=10, max=100)
    assert spec.min == 10
    assert spec.max == 100


def test_rowspec_rejects_invalid_range():
    """Test RowSpec rejects min > max."""
    with pytest.raises(ValidationError) as exc_info:
        RowSpec(min=100, max=10)
    assert "min" in str(exc_info.value).lower()


def test_schema_parses_int_rows():
    """Test schema with integer row count."""
    schema = Schema(
        name="users",
        rows=100,
        attributes=[
            Attribute(name="id", type="random_int")
        ]
    )
    assert schema.rows == 100


def test_schema_parses_dict_rows():
    """Test schema with dict row spec."""
    schema = Schema(
        name="users",
        rows={"min": 10, "max": 100},
        attributes=[
            Attribute(name="id", type="random_int")
        ]
    )
    assert isinstance(schema.rows, RowSpec)
    assert schema.rows.min == 10
    assert schema.rows.max == 100


def test_model_parses_single_locale():
    """Test model with string locale."""
    model = Model(
        name="test",
        locales="en-US",
        schemas=[
            Schema(name="s1", rows=10, attributes=[Attribute(name="id", type="random_int")])
        ]
    )
    assert model.locales == "en-US"


def test_model_parses_list_locale():
    """Test model with list locale (preserved as list)."""
    model = Model(
        name="test",
        locales=["en-US", "fr-FR"],
        schemas=[]
    )
    # Model preserves list locales
    assert isinstance(model.locales, list)
    assert model.locales == ["en-US", "fr-FR"]


def test_model_defaults_locale():
    """Test model defaults locale to en-US."""
    model = Model(name="test", schemas=[])
    assert model.locales == "en-US"


def test_model_defaults_empty_schemas():
    """Test model defaults to empty schemas list."""
    model = Model(name="test", locales="en-US")
    assert model.schemas == []


def test_full_model_from_dict():
    """Test parsing full model from dict (YAML-like structure)."""
    model_dict = {
        "name": "testmodel",
        "locales": ["en-US"],
        "schemas": [
            {
                "name": "dataset1",
                "rows": 100,
                "attributes": [
                    {"name": "id", "type": "random_int", "params": {"min": 1, "max": 100}},
                    {"name": "name", "type": "first_name"}
                ]
            }
        ]
    }
    model = Model(**model_dict)
    assert model.name == "testmodel"
    assert len(model.schemas) == 1
    assert len(model.schemas[0].attributes) == 2
    assert model.schemas[0].attributes[0].params.min == 1

