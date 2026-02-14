# Testing Strategy

This document explains the testing approach for this macOS-targeted Ansible project, what runs where, and why.

## Overview

This project uses a **layered testing strategy** designed to provide **fast feedback on Linux CI** while keeping macOS-specific integration tests as a small, optional layer. This approach balances speed, cost, and confidence.

### Key Principles

1. **Fast feedback first**: Most issues caught on Linux runners (< 2 minutes)
2. **No macOS runner dependency for PRs**: Linux CI validates 80%+ of changes
3. **Minimal tooling**: Standard tools (yamllint, ansible-lint) + lightweight custom scripts
4. **Incremental validation**: Fail fast with clear error messages
5. **Pragmatic over perfect**: Accept false positives; provide clear guidance

## What Runs Where

### Linux CI (Always)

Runs on every PR and push to main branches. Fast, free, and catches most issues.

**Layer 1: YAML Formatting**
- Tool: `yamllint`
- What: Checks YAML syntax, indentation, line length
- Why: Catches syntax errors and formatting issues early
- Runtime: ~10 seconds

**Layer 2: Ansible Syntax**
- Tool: `ansible-playbook --syntax-check`
- What: Validates Ansible playbook syntax without execution
- Why: Catches structural errors (missing quotes, invalid module names, etc.)
- Runtime: ~15 seconds

**Layer 3: Ansible Lint**
- Tool: `ansible-lint`
- What: Enforces Ansible best practices
- Why: Catches common mistakes (prefer modules over shell, naming conventions, etc.)
- Config: `.ansible-lint` (tuned for macOS project)
- Runtime: ~30 seconds

**Layer 4: Structural Validation**
- Tool: Custom Python scripts (see `scripts/`)
- What: Project-specific checks
  - `validate_structure.py`: Role organization, file naming
  - `validate_models.py`: Model declaration format and validity
  - `check_darwin_guards.py`: Ensures macOS-only tasks are guarded
  - `validate_idempotency.py`: Checks shell/command tasks for idempotency
- Why: Catches project-specific anti-patterns and conventions
- Runtime: ~20 seconds

**Total Linux CI runtime: ~2 minutes**

### macOS Integration (Optional)

Runs manually (`workflow_dispatch`) or on a schedule. Uses GitHub-hosted macOS runners (costs money).

**What it does:**
- Runs playbooks on actual macOS in **check mode** (safe, non-destructive)
- Validates fact gathering works on macOS
- Tests Darwin-specific logic paths
- Confirms playbook structure is compatible with macOS

**What it does NOT do:**
- Install Homebrew, Ollama, Docker Desktop (check mode only)
- Download models
- Deploy services
- Test full provisioning (requires dedicated Mac mini)

**When to run:**
- Before major releases
- After significant macOS-specific changes
- On demand for confidence

**Runtime: ~5-10 minutes**

## What's NOT Tested in CI

Some things require a real Mac mini and cannot be tested in CI:

1. **Actual installations**: Homebrew, Ollama, Docker Desktop
2. **Service deployment**: OpenWebUI containers, launchd services
3. **Model downloads**: Large file transfers, Ollama API interaction
4. **Idempotency on macOS**: Re-running playbooks to verify convergence
5. **Upgrades**: Testing version changes end-to-end

**Mitigation**: Manual testing on a dedicated Mac mini before production deployment.

## Running Tests Locally

### Quick validation (recommended before committing)

```bash
make test
```

This runs all the checks that Linux CI will run.

### Individual checks

```bash
# YAML formatting
make lint-yaml
# Or directly:
yamllint .

# Ansible syntax check
ansible-playbook --syntax-check playbooks/site.yml
ansible-playbook --syntax-check playbooks/verify.yml
ansible-playbook --syntax-check playbooks/preflight.yml

# Ansible lint
make lint-ansible
# Or directly:
ansible-lint playbooks/ roles/

# All linting (YAML + Ansible)
make lint

# Custom structural validation
python3 scripts/validate_structure.py
python3 scripts/validate_models.py
python3 scripts/check_darwin_guards.py
python3 scripts/validate_idempotency.py

# All validation scripts
make validate
```

### Full test suite

```bash
make test-all
```

Runs everything: linting + validation scripts.

## Validation Scripts Explained

### `scripts/validate_structure.py`

**Purpose**: Ensure roles follow consistent organization.

**Checks**:
- Each role has `tasks/main.yml`
- Consistent file naming (don't mix `.yml` and `.yaml`)
- Expected directory structure (`defaults/`, `vars/`, etc.)

**Exit codes**:
- 0: All checks passed
- 1: Structural issues found

**Example failure**:
```
❌ Validation errors found:
  - Role 'homebrew' missing tasks/main.yml
  - Role 'ollama' mixes .yml and .yaml extensions in tasks/
```

### `scripts/validate_models.py`

**Purpose**: Validate the `ollama_models` list in `group_vars/all.yml`.

**Checks**:
- Structure is a valid YAML list
- Each model has a `name` field
- No duplicate model names
- Optional `state` field is valid (`present` or `absent`)

**Exit codes**:
- 0: Model declarations are valid
- 1: Validation errors found

**Example failure**:
```
❌ Model validation errors found:
  - Model at index 0 missing required 'name' field
  - Duplicate model name: 'llama3.1:8b'
  - Model 'nomic-embed-text': 'state' must be 'present' or 'absent', got 'installed'
```

### `scripts/check_darwin_guards.py`

**Purpose**: Detect macOS-specific tasks that might not be guarded properly.

**Checks**:
- Tasks using macOS-only patterns (Homebrew, `.app`, `.dmg`, `launchd`, etc.)
- Whether file has Darwin guards (`when: ansible_system == 'Darwin'`)

**Exit codes**:
- 0: No issues or all flagged items reviewed
- (Currently informational only - doesn't fail CI)

**Example warning**:
```
⚠️  Potential unguarded macOS tasks found:
  - playbooks/site.yml: Contains macOS-specific patterns but no Darwin guard: homebrew
```

**Trade-off**: This is heuristic-based and may have false positives. Review each warning.

### `scripts/validate_idempotency.py`

**Purpose**: Encourage idempotent task patterns.

**Checks**:
- `shell`/`command` tasks have `changed_when`, `creates`, or `removes`
- Tasks with `changed_when: true` (idempotency disabled) have comments
- Use of `raw` module (acceptable only in `preflight.yml`)

**Exit codes**:
- 0: No issues or all flagged items reviewed
- (Currently informational only - doesn't fail CI)

**Example warning**:
```
⚠️  Idempotency issues found:
  - site.yml: Task 'Install Homebrew' uses 'shell' without changed_when, creates, or removes
```

**Trade-off**: Some tasks are intentionally non-idempotent if documented. This is guidance, not enforcement.

## Trade-offs and Limitations

### Why not test on macOS for every PR?

**Cost**: macOS runners are 10x more expensive than Linux runners on GitHub Actions.

**Speed**: macOS runners are slower to provision (~2-3 minutes just to start).

**Availability**: Limited concurrency for macOS runners.

**Sufficiency**: Most Ansible issues are caught by syntax/lint checks, not execution.

**Decision**: Use Linux CI for fast feedback; use macOS integration sparingly.

### Why not use Molecule?

**Overhead**: Molecule adds complexity (Docker, test scenarios, extra config).

**macOS limitation**: Molecule is designed for Linux containers; macOS testing requires VMs or real hardware.

**Pragmatism**: This project's needs are met with simpler tools.

**Decision**: Avoid Molecule unless future needs justify it.

### Why custom scripts instead of existing tools?

**Specificity**: Project-specific conventions (model declarations, Darwin guards) not covered by general tools.

**Simplicity**: Lightweight Python scripts (stdlib only) are easy to maintain and debug.

**Speed**: Purpose-built checks are faster than generic frameworks.

**Decision**: Use custom scripts for project-specific validation; use standard tools for general checks.

### Why allow false positives?

**Pragmatism**: Perfect detection requires complex static analysis or execution.

**Speed**: Heuristic checks are fast and catch 90%+ of real issues.

**Clarity**: False positives are reviewable; clear messages help developers decide.

**Decision**: Accept some false positives; provide clear guidance in messages.

## CI Workflow Configuration

### Linux CI (`.github/workflows/ci.yml`)

**Triggers**:
- `pull_request` (any PR)
- `push` to `main` or `develop` branches
- `workflow_dispatch` (manual)

**Jobs** (run in parallel):
1. `lint-yaml`: YAML formatting
2. `ansible-syntax`: Ansible syntax check
3. `ansible-lint`: Ansible best practices
4. `validate-structure`: Role organization
5. `validate-models`: Model declarations
6. `check-darwin-guards`: macOS task guards
7. `check-idempotency`: Idempotency patterns
8. `summary`: Aggregate results (fails if any job failed)

**Pinned versions** (for reproducibility):
- Python: 3.11
- ansible-core: 2.17.0
- yamllint: 1.35.1
- ansible-lint: 26.x (from requirements.txt)
- PyYAML: 6.0.1

### macOS Integration (`.github/workflows/macos-integration.yml`)

**Triggers**:
- `workflow_dispatch` only (manual)
- Optional: scheduled (commented out by default)

**Runner**: `macos-14` (macOS Sonoma, Apple Silicon)

**Jobs**:
1. `macos-check-mode`: Run playbooks in check mode on macOS
2. `macos-summary`: Report results

**What runs**:
- `playbooks/verify.yml` (read-only, should fully work)
- `playbooks/site.yml --check` (dry-run, may fail in check mode)

**Expected behavior**:
- Some tasks fail in check mode (expected for installation tasks)
- Validates playbook can run on macOS without errors in structure

## Continuous Improvement

### Adding new checks

1. Identify a common mistake or anti-pattern
2. Write a lightweight script in `scripts/` (Python preferred)
3. Add a job to `.github/workflows/ci.yml`
4. Document in this file
5. Test locally before committing

### Tuning linters

- **yamllint**: Edit `.yamllint` to adjust rules
- **ansible-lint**: Edit `.ansible-lint` to skip rules or warn instead of fail

**Important**: Document all skipped rules with rationale (see `.ansible-lint`).

### When to run macOS integration

- Before merging to `main` (for critical changes)
- Before releases (always)
- After macOS version updates
- When modifying Darwin-specific logic

## Getting Help

### CI failure: YAML Lint

**Likely cause**: Indentation, line length, or formatting issue.

**Fix**: Run `yamllint .` locally and fix reported issues. Use 2-space indentation consistently.

### CI failure: Ansible Syntax

**Likely cause**: Typo, invalid module name, missing quote, or YAML structure error.

**Fix**: Run `ansible-playbook --syntax-check playbooks/<file>.yml` locally. Read error message carefully.

### CI failure: Ansible Lint

**Likely cause**: Not following Ansible best practices (e.g., using `shell` instead of a module).

**Fix**: Run `ansible-lint playbooks/ roles/` locally. Consider fixing or documenting why skip is needed.

### CI failure: Validation Script

**Likely cause**: Project-specific convention violated (missing `name` in model, no Darwin guard, etc.).

**Fix**: Run the specific script locally (e.g., `python3 scripts/validate_models.py`). Read error message and fix.

### macOS integration failure

**Likely cause**: Task fails in check mode, fact not available, or macOS-specific issue.

**Investigation**: Check workflow logs. Determine if failure is expected (check mode limitation) or real bug.

## Summary

| Layer | Tool | Where | When | Speed | Purpose |
|-------|------|-------|------|-------|---------|
| YAML Formatting | yamllint | Linux CI | Always | 10s | Syntax, style |
| Ansible Syntax | ansible-playbook | Linux CI | Always | 15s | Structural validity |
| Ansible Lint | ansible-lint | Linux CI | Always | 30s | Best practices |
| Structure Validation | Custom scripts | Linux CI | Always | 20s | Role organization |
| Model Validation | Custom scripts | Linux CI | Always | 5s | Model declarations |
| Darwin Guards | Custom scripts | Linux CI | Always | 5s | macOS task guards |
| Idempotency | Custom scripts | Linux CI | Always | 10s | Idempotent patterns |
| macOS Check Mode | ansible-playbook | macOS CI | Manual | 5-10m | macOS compatibility |

**Total Linux CI time: ~2 minutes**  
**Total macOS CI time: ~5-10 minutes**

---

**Last updated**: 2024-02-14  
**Maintained by**: Repository contributors
