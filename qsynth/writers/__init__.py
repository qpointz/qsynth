"""Writers package with registry for output formats."""
from typing import Dict, Type


class WriterRegistry:
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        def _wrap(writer_cls: type):
            cls._registry[name] = writer_cls
            return writer_cls
        return _wrap

    @classmethod
    def get(cls, name: str):
        w = cls._registry.get(name)
        if not w:
            raise Exception(f"Unknown writer '{name}'")
        return w


def register_writer(name: str):
    return WriterRegistry.register(name)


def get_writer(name: str):
    return WriterRegistry.get(name)()


