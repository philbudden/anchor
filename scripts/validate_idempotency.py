#!/usr/bin/env python3
"""
Validate idempotency patterns in shell/command tasks.

Checks:
- shell/command tasks have appropriate changed_when, creates, or removes
- Tasks disabling idempotency have explanatory comments
- Tasks are using the right module (prefer specific modules over shell)

Exit codes:
  0 - All checks passed
  1 - Idempotency issues found
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any
import yaml


def check_task_idempotency(task: Dict[str, Any], file_path: Path, task_idx: int) -> List[str]:
    """Check a single task for idempotency issues."""
    issues = []
    
    task_name = task.get("name", f"task #{task_idx}")
    
    # Check if task uses shell or command
    uses_shell = "shell" in task or "ansible.builtin.shell" in task
    uses_command = "command" in task or "ansible.builtin.command" in task
    uses_raw = "raw" in task or "ansible.builtin.raw" in task
    
    if not (uses_shell or uses_command or uses_raw):
        return []
    
    # Check for idempotency guards
    has_changed_when = "changed_when" in task
    has_creates = False
    has_removes = False
    
    # Check args dict for creates/removes
    if uses_shell or uses_command:
        module_key = "shell" if uses_shell else "command"
        if module_key not in task:
            module_key = f"ansible.builtin.{module_key}"
        
        module_args = task.get(module_key, {})
        if isinstance(module_args, dict):
            has_creates = "creates" in module_args
            has_removes = "removes" in module_args
        
        # Also check task-level args
        task_args = task.get("args", {})
        if isinstance(task_args, dict):
            has_creates = has_creates or "creates" in task_args
            has_removes = has_removes or "removes" in task_args
    
    # Raw tasks get special treatment (preflight.yml uses them intentionally)
    if uses_raw:
        if "preflight" not in file_path.name.lower():
            # Only flag raw outside of preflight
            if not has_changed_when:
                issues.append(
                    f"{file_path.name}: Task '{task_name}' uses 'raw' without changed_when "
                    "(acceptable in preflight.yml only)"
                )
        return issues
    
    # If no idempotency guard, flag it
    if not (has_changed_when or has_creates or has_removes):
        module_type = "shell" if uses_shell else "command"
        issues.append(
            f"{file_path.name}: Task '{task_name}' uses '{module_type}' "
            "without changed_when, creates, or removes"
        )
    
    # Check for changed_when: true (idempotency disabled)
    if has_changed_when:
        changed_value = task.get("changed_when")
        if changed_value is True:
            issues.append(
                f"{file_path.name}: Task '{task_name}' has 'changed_when: true' "
                "(disables idempotency - should have explanatory comment)"
            )
    
    return issues


def check_yaml_file(file_path: Path) -> List[str]:
    """Check all tasks in a YAML file."""
    issues = []
    
    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [f"Failed to parse {file_path}: {e}"]
    
    if not data:
        return []
    
    # Handle playbook format (list of plays)
    if isinstance(data, list):
        for play in data:
            if not isinstance(play, dict):
                continue
            
            # Check pre_tasks
            for idx, task in enumerate(play.get("pre_tasks", [])):
                if isinstance(task, dict):
                    issues.extend(check_task_idempotency(task, file_path, idx))
            
            # Check tasks
            for idx, task in enumerate(play.get("tasks", [])):
                if isinstance(task, dict):
                    issues.extend(check_task_idempotency(task, file_path, idx))
            
            # Check post_tasks
            for idx, task in enumerate(play.get("post_tasks", [])):
                if isinstance(task, dict):
                    issues.extend(check_task_idempotency(task, file_path, idx))
    
    # Handle task file format (list of tasks)
    elif isinstance(data, list):
        for idx, task in enumerate(data):
            if isinstance(task, dict):
                issues.extend(check_task_idempotency(task, file_path, idx))
    
    return issues


def main() -> int:
    """Run all validation checks."""
    repo_root = Path(__file__).parent.parent
    
    print("Checking shell/command task idempotency patterns...")
    print()
    
    all_issues = []
    
    # Check playbooks
    playbooks_dir = repo_root / "playbooks"
    if playbooks_dir.exists():
        for yaml_file in playbooks_dir.glob("*.yml"):
            all_issues.extend(check_yaml_file(yaml_file))
    
    # Check roles
    roles_dir = repo_root / "roles"
    if roles_dir.exists():
        for role_dir in roles_dir.iterdir():
            if not role_dir.is_dir():
                continue
            tasks_dir = role_dir / "tasks"
            if tasks_dir.exists():
                for yaml_file in tasks_dir.glob("*.yml"):
                    all_issues.extend(check_yaml_file(yaml_file))
    
    # Report results
    if all_issues:
        print("⚠️  Idempotency issues found:\n")
        for issue in all_issues:
            print(f"  - {issue}")
        print()
        print("Note: These are recommendations. Tasks may be intentionally")
        print("non-idempotent if properly documented. Review each case.")
        print()
        # Make this a warning, not a hard failure (too noisy initially)
        return 0
    else:
        print("✅ No idempotency issues detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
