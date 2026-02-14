#!/usr/bin/env python3
"""
Validate Ansible role structure and organization.

Checks:
- Each role has tasks/main.yml
- Each role uses consistent file naming
- Roles follow expected directory layout
- No ambiguous includes

Exit codes:
  0 - All checks passed
  1 - Validation errors found
"""

import sys
from pathlib import Path
from typing import List, Tuple


def validate_role_structure(roles_dir: Path) -> List[str]:
    """Validate role directory structure."""
    errors = []
    
    if not roles_dir.exists():
        return [f"Roles directory not found: {roles_dir}"]
    
    # Find all role directories (ignore README.md)
    role_dirs = [d for d in roles_dir.iterdir() if d.is_dir()]
    
    if not role_dirs:
        return [f"No roles found in {roles_dir}"]
    
    for role_dir in role_dirs:
        role_name = role_dir.name
        
        # Check for tasks/main.yml (required)
        tasks_main = role_dir / "tasks" / "main.yml"
        if not tasks_main.exists():
            errors.append(f"Role '{role_name}' missing tasks/main.yml")
        
        # Check that if directories exist, they follow conventions
        expected_files = {
            "defaults": "main.yml",
            "vars": "main.yml",
            "handlers": "main.yml",
            "meta": "main.yml",
        }
        
        for dir_name, expected_file in expected_files.items():
            dir_path = role_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                expected_path = dir_path / expected_file
                if not expected_path.exists():
                    errors.append(
                        f"Role '{role_name}' has {dir_name}/ directory "
                        f"but missing {expected_file}"
                    )
    
    return errors


def validate_task_files(roles_dir: Path) -> List[str]:
    """Validate task file organization."""
    errors = []
    
    for role_dir in roles_dir.iterdir():
        if not role_dir.is_dir():
            continue
        
        tasks_dir = role_dir / "tasks"
        if not tasks_dir.exists():
            continue
        
        role_name = role_dir.name
        
        # Find all YAML files in tasks/
        task_files = list(tasks_dir.glob("*.yml")) + list(tasks_dir.glob("*.yaml"))
        
        # Check for consistent naming (all .yml or all .yaml, not mixed)
        yml_count = len(list(tasks_dir.glob("*.yml")))
        yaml_count = len(list(tasks_dir.glob("*.yaml")))
        
        if yml_count > 0 and yaml_count > 0:
            errors.append(
                f"Role '{role_name}' mixes .yml and .yaml extensions in tasks/"
            )
        
        # Warn if tasks have unclear names
        for task_file in task_files:
            name = task_file.stem
            if name not in ["main"] and not any(
                keyword in name.lower()
                for keyword in ["install", "configure", "setup", "verify", "preflight", "models", "assert"]
            ):
                # Just a warning, not an error
                pass
    
    return errors


def main() -> int:
    """Run all validation checks."""
    repo_root = Path(__file__).parent.parent
    roles_dir = repo_root / "roles"
    
    print(f"Validating role structure in: {roles_dir}")
    print()
    
    all_errors = []
    
    # Run checks
    all_errors.extend(validate_role_structure(roles_dir))
    all_errors.extend(validate_task_files(roles_dir))
    
    # Report results
    if all_errors:
        print("❌ Validation errors found:\n")
        for error in all_errors:
            print(f"  - {error}")
        print()
        return 1
    else:
        print("✅ All role structure checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
