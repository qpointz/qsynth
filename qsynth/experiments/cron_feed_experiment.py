"""Cron feed experiment - generates data on schedule."""
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from croniter import croniter

from qsynth.experiments.base import Experiment
from qsynth.experiments import register_experiment
from qsynth.models import Model
from qsynth.main import MultiModelsFaker
from qsynth.writers import get_writer


@register_experiment('cron_feed')
class CronFeedExperiment(Experiment):
    """Experiment that generates data files on a cron schedule."""
    
    def __init__(self, config: Dict[str, Any], models: List[Model], relative_to: Optional[Path] = None):
        super().__init__(config, models, relative_to)
        self.cron = config['cron']
        self.dates = config['dates']
        self.path_template = config['path']
        self.writer_config = config['writer']
    
    def run(self) -> None:
        """Generate data files for each cron occurrence in the date range."""
        # Parse date range
        datesp = self.dates
        from_date = datetime.now()
        to_date = datetime.max
        count = sys.maxsize
        
        if 'to' not in datesp and 'count' not in datesp:
            raise ValueError("One of parameters 'to' or 'count' must be present")
        
        if 'from' in datesp:
            from_date = datetime.strptime(datesp['from'], '%Y-%m-%d')
        if 'to' in datesp:
            to_date = datetime.strptime(datesp['to'], '%Y-%m-%d')
        if 'count' in datesp:
            count = datesp['count']
        
        if from_date >= to_date:
            raise ValueError("'from_date' cannot be greater than 'to_date'")
        
        # Setup writer
        writer = get_writer(self.writer_config['name'])
        write_params = self.writer_config.get('params', {})
        
        # Generate data for each cron occurrence
        i = 0
        cron_iter = croniter(self.cron, from_date)
        cur_date = from_date
        
        while i < count and cur_date <= to_date:
            cur_date = cron_iter.next(datetime)
            print(cur_date)
            
            # Generate data
            mmf = MultiModelsFaker(self.models)
            mmf.generate_all()
            
            # Write each dataset
            for model_name, model_faker in mmf.models.items():
                for dataset_name, dataframe in model_faker.generated.items():
                    path_vars = {
                        'model-name': model_name,
                        'dataset-name': dataset_name,
                        'cron-date': cur_date
                    }
                    output_path = self._resolve_path(self.path_template, **path_vars)
                    writer.write(output_path, dataframe, model_name, dataset_name, model_faker, write_params)
            
            i += 1

