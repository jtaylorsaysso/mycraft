
import sys
import os

print(f"Python: {sys.executable}")
print("Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import direct
    print(f"Direct imported from: {direct}")
    print(f"Direct file: {getattr(direct, '__file__', 'None')}")
    print(f"Direct path: {getattr(direct, '__path__', 'None')}")
except ImportError as e:
    print(f"Import error: {e}")

try:
    import direct.fsm
    print("direct.fsm imported!")
except ImportError as e:
    print(f"direct.fsm error: {e}")
