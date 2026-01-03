
import sys
import os

sys.path.append(os.getcwd())

def verify_imports():
    print("Verifying Scaffolding Imports...")
    
    try:
        from engine.ui.editors.map_editor import MapEditorWindow
        print("✅ engine.ui.editors.map_editor imported")
    except ImportError as e:
        print(f"❌ Failed to import map_editor: {e}")
        
    try:
        from engine.ui.editors.voxel_model_editor import VoxelModelEditorWindow
        print("✅ engine.ui.editors.voxel_model_editor imported")
    except ImportError as e:
        print(f"❌ Failed to import voxel_model_editor: {e}")
        
    try:
        from engine.ui.widgets.inspector_widget import InspectorWidget
        print("✅ engine.ui.widgets.inspector_widget imported")
    except ImportError as e:
        print(f"❌ Failed to import inspector_widget: {e}")
        
    try:
        from engine.ui.widgets.hierarchy_widget import HierarchyWidget
        print("✅ engine.ui.widgets.hierarchy_widget imported")
    except ImportError as e:
        print(f"❌ Failed to import hierarchy_widget: {e}")
        
    try:
        from engine.ui.widgets.asset_browser import AssetBrowserWidget
        print("✅ engine.ui.widgets.asset_browser imported")
    except ImportError as e:
        print(f"❌ Failed to import asset_browser: {e}")
        
    print("Verification Complete.")

if __name__ == "__main__":
    verify_imports()
