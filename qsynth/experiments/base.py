"""Base experiment class and configuration."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from qsynth.models import Model


class ExperimentConfig(BaseModel):
    """Base configuration for all experiments."""
    type: str = Field(description="Experiment type identifier")
    path: str = Field(description="Output path template (supports {model-name}, {dataset-name})")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional experiment parameters")


class Experiment(ABC):
    """Base class for all experiments."""
    
    def __init__(self, config: Dict[str, Any], models: List[Model], relative_to: Optional[Path] = None):
        """
        Initialize experiment.
        
        Args:
            config: Experiment configuration dictionary
            models: List of Model objects to use
            relative_to: Base path for resolving relative paths (should be parent of YAML file)
        """
        self.config_dict = config
        self.models = models
        # relative_to should already be the parent directory (set in Experiments.__init__)
        self.relative_to = relative_to if relative_to else Path.cwd()
    
    @abstractmethod
    def run(self) -> None:
        """Execute the experiment."""
        pass
    
    def _resolve_path(self, path_template: str, **kwargs) -> Path:
        """Resolve path template with variables."""
        resolved = path_template.format(**kwargs)
        return (self.relative_to / resolved).absolute()

