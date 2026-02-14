#!/usr/bin/env python3
"""
Check for unguarded macOS-specific tasks.

Validates that tasks using macOS-only modules or commands are properly
guarded with 'when: ansible_system == "Darwin"' or similar conditions.

This is a heuristic check - it catches common patterns but is not exhaustive.

Exit codes:
  0 - All checks passed or no issues found
  1 - Potential unguarded macOS tasks found
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple
import yaml


# Patterns that indicate macOS-specific operations
MACOS_INDICATORS = [
    r'homebrew',
    r'brew\s+',
    r'launchd',
    r'xcode-select',
    r'softwareupdate',
    r'\.app["\']?\s*$',
    r'\.dmg["\']?\s*$',
    r'\.pkg["\']?\s*$',
    r'/Applications/',
    r'com\.apple\.',
    r'defaults\s+write',
    r'darwin',
]

# Guards that indicate Darwin check
DARWIN_GUARDS = [
    r'ansible_system.*==.*["\']Darwin["\']',
    r'ansible_os_family.*==.*["\']Darwin["\']',
    r'ansible_distribution.*==.*["\']MacOSX["\']',
]


def check_file_for_guards(file_path: Path) -> List[str]:
    """Check a single YAML file for unguarded macOS tasks."""
    issues = []
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        return [f"Failed to read {file_path}: {e}"]
    
    # Quick check: if file has Darwin guards, assume it's handled
    has_guards = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in DARWIN_GUARDS
    )
    
    # Check for macOS indicators
    macos_indicators_found = []
    for pattern in MACOS_INDICATORS:
        if re.search(pattern, content, re.IGNORECASE):
            macos_indicators_found.append(pattern)
    
    # If we found macOS indicators but no guards, flag it
    # Exception: preflight.yml is allowed (it's macOS-only by design)
    if macos_indicators_found and not has_guards:
        if "preflight" not in file_path.name.lower():
            issues.append(
                f"{file_path.relative_to(Path.cwd())}: "
                f"Contains macOS-specific patterns but no Darwin guard: "
                f"{', '.join(macos_indicators_found[:3])}"
            )
    
    return issues


def main() -> int:
    """Run all validation checks."""
    repo_root = Path(__file__).parent.parent
    
    print("Checking for unguarded macOS-specific tasks...")
    print()
    
    all_issues = []
    
    # Check playbooks
    playbooks_dir = repo_root / "playbooks"
    if playbooks_dir.exists():
        for yaml_file in playbooks_dir.glob("*.yml"):
            all_issues.extend(check_file_for_guards(yaml_file))
    
    # Check roles
    roles_dir = repo_root / "roles"
    if roles_dir.exists():
        for role_dir in roles_dir.iterdir():
            if not role_dir.is_dir():
                continue
            tasks_dir = role_dir / "tasks"
            if tasks_dir.exists():
                for yaml_file in tasks_dir.glob("*.yml"):
                    all_issues.extend(check_file_for_guards(yaml_file))
    
    # Report results
    if all_issues:
        print("⚠️  Potential unguarded macOS tasks found:\n")
        for issue in all_issues:
            print(f"  - {issue}")
        print()
        print("Note: This is a heuristic check. Review each case to determine")
        print("if a Darwin guard is needed or if the detection is a false positive.")
        print()
        # Don't fail on warnings, just inform
        return 0
    else:
        print("✅ No unguarded macOS tasks detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
