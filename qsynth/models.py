"""Strictly typed Pydantic models for qsynth configuration schemas."""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class RowSpec(BaseModel):
    """Row count specification - either exact number or min/max range."""
    min: int = Field(default=0, ge=0)
    max: int = Field(default=10000, ge=0)

    @model_validator(mode='after')
    def validate_range(self):
        if self.min > self.max:
            raise ValueError(f"min ({self.min}) cannot be greater than max ({self.max})")
        return self


RowCount = Union[int, RowSpec]


class RefParams(BaseModel):
    """Parameters for ${ref} type attributes."""
    dataset: str = Field(description="Name of the referenced dataset")
    attribute: str = Field(description="Name of the referenced attribute")
    cord: Optional[str] = Field(default="1-*", description="Cardinality")


class AttributeParams(BaseModel):
    """Flexible params structure for different attribute generators."""
    # For ${ref}
    dataset: Optional[str] = None
    attribute: Optional[str] = None
    cord: Optional[str] = None
    
    # For random_int, random_double
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    
    # For random_element
    elements: Optional[List[Any]] = None
    
    # For lexify and similar
    text: Optional[str] = None
    letters: Optional[str] = None
    
    # Allow any additional params
    model_config = {"extra": "allow"}


class Attribute(BaseModel):
    """A single attribute/column definition."""
    name: str = Field(description="Attribute name")
    type: str = Field(description="Generator type (e.g., 'random_int', '${ref}', 'first_name')")
    params: Optional[AttributeParams] = Field(default=None, description="Generator parameters")
    description: Optional[str] = Field(default=None, description="Optional attribute description")

    @field_validator('params', mode='before')
    @classmethod
    def parse_params(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return AttributeParams(**v)
        return v


class Schema(BaseModel):
    """A dataset schema definition."""
    name: str = Field(description="Schema/dataset name")
    rows: RowCount = Field(description="Row count specification")
    attributes: List[Attribute] = Field(description="List of attributes")
    description: Optional[str] = Field(default=None, description="Optional schema description")

    @field_validator('rows', mode='before')
    @classmethod
    def parse_rows(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, dict):
            return RowSpec(**v)
        raise ValueError(f"rows must be int or dict with min/max, got {type(v)}")


class Model(BaseModel):
    """A complete model definition with multiple schemas."""
    name: str = Field(description="Model name")
    locales: Union[str, List[str]] = Field(default="en-US", description="Locale(s) for faker")
    schemas: List[Schema] = Field(default_factory=list, description="List of schemas")

    @field_validator('locales', mode='before')
    @classmethod
    def parse_locales(cls, v):
        if v is None:
            return "en-US"
        # Keep list as-is, don't convert to string
        if isinstance(v, list):
            return v if v else ["en-US"]
        return v


class ExperimentConfig(BaseModel):
    """Base experiment configuration."""
    type: str = Field(description="Experiment type")
    path: str = Field(description="Output path template")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameters")


class CronFeedExperimentConfig(ExperimentConfig):
    """Configuration for cron_feed experiments."""
    type: str = Field(default="cron_feed")
    cron: str = Field(description="Cron expression")
    dates: Dict[str, Any] = Field(description="Date range specification")
    writer: Dict[str, Any] = Field(description="Writer configuration")

