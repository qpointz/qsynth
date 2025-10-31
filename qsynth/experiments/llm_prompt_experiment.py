"""LLM prompt write experiment."""
from qsynth.experiments.write_experiment import WriteExperiment
from qsynth.experiments import register_experiment
from qsynth.writers.llm_prompt_writer import LLMPromptWriter


@register_experiment('llm-prompt')
class LLMPromptWriteExperiment(WriteExperiment):
    """Experiment to write LLM prompt describing the database schema."""
    
    def get_writer(self):
        return LLMPromptWriter()

