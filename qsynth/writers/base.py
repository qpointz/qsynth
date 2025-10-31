from abc import abstractmethod
import os
import re
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

    @staticmethod
    def clean_type_name(s):
        """Clean type name by removing parenthetical annotations."""
        typec = r"\([^)]+\)"
        return re.sub(typec, '', str(s).lower())

    @staticmethod
    def to_sql_type(dk):
        """Convert numpy dtype kind to SQL type."""
        match dk:
            case 'i':
                return 'INT'
            case 'O':
                return 'VARCHAR'
            case 'f':
                return 'DECIMAL(15,4)'
            case 'M':
                return 'DATE'
            case _:
                raise Exception(f"Unknown type kind {dk}")


