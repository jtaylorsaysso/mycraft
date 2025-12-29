"""
Component base classes for ECS.
"""
from typing import Type, TypeVar, Dict, Any
from dataclasses import dataclass

@dataclass
class Component:
    """
    Base class for all ECS components. 
    Components should be pure data classes.
    """
    pass

# Registry to map string names to Component classes (for config loading)
_COMPONENT_REGISTRY: Dict[str, Type[Component]] = {}

def register_component(cls):
    """Decorator to register a component class by name."""
    _COMPONENT_REGISTRY[cls.__name__] = cls
    return cls

def get_component_class(name: str) -> Type[Component]:
    """Retrieve component class by name."""
    return _COMPONENT_REGISTRY.get(name)
