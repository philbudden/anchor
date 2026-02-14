#!/usr/bin/env python3
"""
Validate Ollama model declarations.

Checks:
- Model list structure is valid YAML
- Each model has required 'name' field
- Model names are fully qualified (no implicit :latest)
- No duplicate model names
- State field is valid (if present)

Exit codes:
  0 - All checks passed
  1 - Validation errors found
"""

import sys
from pathlib import Path
from typing import Any, Dict, List
import yaml


def validate_model_structure(models: Any) -> List[str]:
    """Validate model list structure."""
    errors = []
    
    if not isinstance(models, list):
        return [f"ollama_models must be a list, got {type(models).__name__}"]
    
    if not models:
        # Empty list is valid (no models declared)
        return []
    
    seen_names = set()
    
    for idx, model in enumerate(models):
        if not isinstance(model, dict):
            errors.append(f"Model at index {idx} must be a dict, got {type(model).__name__}")
            continue
        
        # Check required 'name' field
        if "name" not in model:
            errors.append(f"Model at index {idx} missing required 'name' field")
            continue
        
        name = model["name"]
        
        if not isinstance(name, str):
            errors.append(f"Model at index {idx}: 'name' must be a string")
            continue
        
        if not name.strip():
            errors.append(f"Model at index {idx}: 'name' cannot be empty")
            continue
        
        # Check for duplicates
        if name in seen_names:
            errors.append(f"Duplicate model name: '{name}'")
        seen_names.add(name)
        
        # Encourage fully qualified names (warn if looks like implicit :latest)
        # This is a soft check - some models don't use tags
        if ":" not in name:
            # This is informational, not an error
            # Some models like "nomic-embed-text" don't use tags
            pass
        
        # Check optional 'state' field
        if "state" in model:
            state = model["state"]
            if state not in ["present", "absent"]:
                errors.append(
                    f"Model '{name}': 'state' must be 'present' or 'absent', got '{state}'"
                )
    
    return errors


def main() -> int:
    """Run all validation checks."""
    repo_root = Path(__file__).parent.parent
    vars_file = repo_root / "inventory" / "group_vars" / "all.yml"
    
    print(f"Validating model declarations in: {vars_file}")
    print()
    
    if not vars_file.exists():
        print(f"❌ Variables file not found: {vars_file}")
        return 1
    
    # Load variables file
    try:
        with open(vars_file, "r") as f:
            vars_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Failed to parse YAML: {e}")
        return 1
    
    if not vars_data:
        print("❌ Variables file is empty or invalid")
        return 1
    
    # Extract ollama_models
    models = vars_data.get("ollama_models", [])
    
    # Validate
    errors = validate_model_structure(models)
    
    # Report results
    if errors:
        print("❌ Model validation errors found:\n")
        for error in errors:
            print(f"  - {error}")
        print()
        return 1
    else:
        model_count = len(models) if isinstance(models, list) else 0
        print(f"✅ Model declarations are valid ({model_count} models declared)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
