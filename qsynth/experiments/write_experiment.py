"""Base class for write experiments."""
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import abstractmethod

from qsynth.experiments.base import Experiment
from qsynth.models import Model
from qsynth.main import MultiModelsFaker
from qsynth.writers.base import Writer


class WriteExperiment(Experiment):
    """Base class for experiments that write data to files."""
    
    def __init__(self, config: Dict[str, Any], models: List[Model], relative_to: Optional[Path] = None):
        super().__init__(config, models, relative_to)
        self.path_template = config['path']
        self.write_params = config.get('params', {})
    
    def run(self) -> None:
        """Generate data and write using the configured writer."""
        mmf = MultiModelsFaker(self.models)
        mmf.generate_all()
        
        writer = self.get_writer()
        
        # Initialize writer with first model/dataset path (if needed) or base directory
        # Use a dummy path for init if template has variables
        if '{' in self.path_template:
            # Path has variables, use a sample path for init
            first_model = next(iter(mmf.models.keys())) if mmf.models else None
            first_dataset = None
            if first_model and mmf.models[first_model].generated:
                first_dataset = next(iter(mmf.models[first_model].generated.keys()))
            
            if first_model and first_dataset:
                init_path = self._resolve_path(
                    self.path_template,
                    **{'model-name': first_model, 'dataset-name': first_dataset}
                )
            else:
                # Fallback: use directory from template
                from pathlib import Path
                init_path = (self.relative_to / Path(self.path_template).parent).absolute()
        else:
            init_path = self._resolve_path(self.path_template)
        
        writer.init_writer(init_path)
        
        # Write each generated dataset
        for model_name, model_faker in mmf.models.items():
            for dataset_name, dataframe in model_faker.generated.items():
                path_vars = {
                    'model-name': model_name,
                    'dataset-name': dataset_name
                }
                output_path = self._resolve_path(self.path_template, **path_vars)
                writer.write(output_path, dataframe, model_name, dataset_name, model_faker, self.write_params)
        
        writer.finalize_writer()
    
    @abstractmethod
    def get_writer(self) -> Writer:
        """Return the writer instance for this experiment type."""
        pass

