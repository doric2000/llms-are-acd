import sys

def check_import(module_path, message, required=True):
    try:
        exec(f"import {module_path}")
        print(f"{message}")
        return True
    except Exception as e:
        if required:
            print(f"Failed to import {module_path}: {e}")
            return False
        else:
            print(f"Optional module not available: {module_path}")
            return True

success = True
success &= check_import("CybORG", "CybORG core package")
success &= check_import("CybORG.Agents.SimpleAgents", "SimpleAgents")  
success &= check_import("CybORG.Simulator.Scenarios", "Scenarios")
success &= check_import("torch", "PyTorch")
success &= check_import("torch_geometric", "PyTorch Geometric")
success &= check_import("numpy", "NumPy")
success &= check_import("gym", "Gym")
success &= check_import("gymnasium", "Gymnasium")
success &= check_import("ray", "Ray")

if success:
    print("\n Core packages imported successfully!")
    sys.exit(0)
else:
    print("\n Some core imports failed. Please check the error messages above.")
    sys.exit(1)
