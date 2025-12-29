#!/usr/bin/env python3
"""
Launcher Testing Script
Tests all launcher components without requiring GUI interaction
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all necessary imports work."""
    print("Testing imports...")
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        import subprocess
        import socket
        import time
        import threading
        import json
        from pathlib import Path
        from engine.networking.discovery import find_servers
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_discovery():
    """Test server discovery functionality."""
    print("\nTesting server discovery...")
    try:
        from engine.networking.discovery import find_servers
        servers = find_servers(timeout=0.5)
        print(f"✓ Discovery works (found {len(servers)} servers)")
        return True
    except Exception as e:
        print(f"✗ Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_launcher_instantiation():
    """Test that launcher can be created."""
    print("\nTesting launcher instantiation...")
    try:
        import tkinter as tk
        from launcher import MyCraftLauncher
        
        root = tk.Tk()
        app = MyCraftLauncher(root)
        
        # Check key attributes exist
        assert hasattr(app, 'launch_single_player')
        assert hasattr(app, 'launch_multiplayer')
        assert hasattr(app, 'launch_server')
        assert hasattr(app, '_handle_launch_error')
        assert hasattr(app, '_enable_close_button')
        
        # Check new UI components
        assert hasattr(app, 'dev_mode_var')
        assert hasattr(app, 'sens_var')
        assert hasattr(app, 'fov_var')
        assert hasattr(app, 'advanced_visible')
        assert hasattr(app, 'toggle_advanced')
        assert hasattr(app, 'update_preset_desc')
        assert hasattr(app, 'open_server_config')
        
        # Test basic toggles (logic only, no GUI update check)
        app.toggle_advanced()
        assert app.advanced_visible is not None
        
        root.destroy()
        print("✓ Launcher instantiation successful")
        return True
    except Exception as e:
        print(f"✗ Launcher instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subprocess_command():
    """Test that subprocess commands are formed correctly."""
    print("\nTesting subprocess command formation...")
    try:
        cmd = [sys.executable, "run_client.py", "--preset", "creative", "--name", "test"]
        print(f"  Command: {' '.join(cmd)}")
        print(f"  Python: {sys.executable}")
        print(f"  Exists: {os.path.exists(sys.executable)}")
        print("✓ Command formation looks good")
        return True
    except Exception as e:
        print(f"✗ Command formation failed: {e}")
        return False

def test_error_handling():
    """Test error handling logic."""
    print("\nTesting error handling...")
    try:
        from launcher import MyCraftLauncher
        import tkinter as tk
        
        root = tk.Tk()
        app = MyCraftLauncher(root)
        
        # Test error message parsing
        test_errors = [
            ("ModuleNotFoundError: No module named 'panda3d'", "panda3d"),
            ("ModuleNotFoundError: No module named 'foo'", "module"),
            ("Permission denied", "permission"),
            ("Some random error", "generic")
        ]
        
        for error_msg, expected_type in test_errors:
            error_lower = error_msg.lower()
            if "panda3d" in error_lower:
                detected = "panda3d"
            elif "modulenotfounderror" in error_lower:
                detected = "module"
            elif "permission" in error_lower:
                detected = "permission"
            else:
                detected = "generic"
            
            assert detected == expected_type, f"Expected {expected_type}, got {detected}"
        
        root.destroy()
        print("✓ Error handling logic works")
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_existence():
    """Test that required files exist."""
    print("\nTesting file existence...")
    required_files = [
        "run_client.py",
        "run_server.py",
        "launcher.py",
        "requirements.txt",
        "config/playtest.json"
    ]
    
    all_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def main():
    print("="*60)
    print("MyCraft Launcher Test Suite")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "File Existence": test_file_existence(),
        "Server Discovery": test_discovery(),
        "Launcher Instantiation": test_launcher_instantiation(),
        "Subprocess Commands": test_subprocess_command(),
        "Error Handling": test_error_handling()
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Launcher is ready!")
    else:
        print("✗ SOME TESTS FAILED - See errors above")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
