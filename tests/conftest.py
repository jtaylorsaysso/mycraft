"""Test configuration and shared fixtures."""
import pytest
import sys


# Module-level cleanup - runs after an entire test module finishes
_module_cleanup_callbacks = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_module_mocks():
    """Clean up module-level mocks after each test module completes."""
    yield
    
    # After entire module: remove mocked ursina to prevent pollution
    # Only remove if it's a mock (has _mock_name attribute)
    ursina_module = sys.modules.get('ursina')
    if ursina_module and hasattr(ursina_module, '_mock_name'):
        sys.modules.pop('ursina', None)
