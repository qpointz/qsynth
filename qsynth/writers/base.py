from abc import abstractmethod
import os
from pandas import DataFrame


class Writer:

    @abstractmethod
    def init_writer(self, init_path):
        print(f"Init writer on {init_path}")

    @abstractmethod
    def finalize_writer(self):
        print(f"Finalize writer on")

    @abstractmethod
    def write(self, path, pd: DataFrame, model_name, schema_name, model, writeparams={}):
        pass

    @staticmethod
    def ensure_path(path):
        if os.path.exists(path):
            os.remove(path)
        else:
            if not os.path.exists(path.parent):
                os.makedirs(path.parent)


