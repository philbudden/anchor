# Roles Structure

This directory contains Ansible roles for provisioning the Mac mini local LLM server.

## Role Organization

Each role is responsible for a specific subsystem and follows the separation of concerns principle from AGENTS.md:

### `common/`
**Responsibility:** Shared setup, assertions, and preconditions.

Tasks:
- Directory structure creation and permissions
- Preflight checks and system assertions
- Firewall rules (if needed)
- Shared defaults and facts

Used by: All other roles as a baseline.

### `homebrew/`
**Responsibility:** Homebrew installation and package management.

Tasks:
- Install Homebrew (detect existing, do not clobber)
- Ensure brew is available to Ansible
- Install required packages (explicit list, pinned versions)
- Avoid `brew upgrade` by default; upgrades are opt-in

Configuration:
- Pinned versions in `group_vars/all.yml`
- Safety mode: `enable_upgrades`

### `ollama/`
**Responsibility:** Ollama LLM runtime installation and management.

Tasks:
- Download and install Ollama (pinned version)
- Configure Ollama service (launchd integration)
- Ensure stable models directory
- Health checks (API connectivity)

Configuration:
- Pinned version: `ollama_version`
- API host/port: `ollama_api_host`, `ollama_api_port`
- Models directory: `ollama_models_dir`

### `docker_desktop/`
**Responsibility:** Docker Desktop installation and Docker CLI availability.

Tasks:
- Download and install Docker Desktop (macOS, pinned version)
- Check if Docker daemon is running
- If not running: **fail with clear instructions** for manual Docker startup
- User must start Docker Desktop and re-run playbook

Behavior:
- **Explicit failure:** If Docker daemon is not running after installation, the playbook fails with formatted instructions
- **Idempotent re-run:** After user starts Docker, re-running the playbook skips completed steps and continues
- **Clear guidance:** Failure message includes step-by-step instructions and IP address of target Mac
- **Skip option:** Can be bypassed with `-e docker_startup_skip_check=true` (not recommended)

Configuration:
- Pinned version: `docker_desktop_version`
- User context for Docker access

### `models/`
**Responsibility:** Ollama model reconciliation.

Tasks:
- Pull declared models (ensure present)
- Idempotent: skip if already present
- Optional: Refresh (repull) all models
- Optional: Prune unmanaged models (dangerous; off by default)

Configuration:
- Model list: `ollama_models` (single source of truth)
- Modes: `ollama_models_refresh`, `ollama_models_prune`

### `openwebui/`
**Responsibility:** OpenWebUI container deployment and service management.

Tasks:
- Deploy Docker Compose from `compose/openwebui/compose.yml`
- Load environment from `.env` file
- Configure named volumes or bind mounts
- Health checks (container up, port responsive)
- Manage container lifecycle

Configuration:
- Image tag: `openwebui_image_tag`
- API host/port: `openwebui_api_host`, `openwebui_api_port`
- Data directory: `openwebui_data_dir`
- Container name: `openwebui_container_name`

## Role Defaults

Each role should define sensible defaults in `roles/<role>/defaults/main.yml`:

```yaml
# Example: roles/ollama/defaults/main.yml
ollama_version: "0.3.0"
ollama_api_host: "127.0.0.1"
ollama_api_port: 11434
```

These are overridden by `group_vars/all.yml` and command-line extra variables.

## Role Variables

Each role should document its variables in `roles/<role>/README.md`:

```markdown
# Ollama Role

Installs and manages Ollama LLM runtime.

## Variables

- `ollama_version` (default: "0.3.0") — Pinned Ollama version
- `ollama_api_host` (default: "127.0.0.1") — Bind address
- `ollama_api_port` (default: 11434) — Bind port
- `ollama_models_dir` (default: "/opt/local-llm/ollama/models") — Models storage

...
```

## Tasks and Handlers

Each role should include:

- `tasks/main.yml` — Main tasks
- `handlers/main.yml` (if needed) — Service reload/restart handlers
- `templates/` — Config file templates (if needed)
- `files/` — Static files (if needed)

Avoid:
- Raw shell scripts (prefer Ansible modules)
- Interactive prompts (not suitable for automation)
- Side effects like creating files in user home or temp dirs

## Testing

For each role:

1. Run lint: `ansible-lint roles/<role>`
2. Run in check mode: `ansible-playbook playbooks/site.yml --tags <role> --check`
3. Verify idempotency: Run twice, confirm no unexpected changes on second run

## Versioning and Upgrades

When adding or updating a role:

1. Pin all versions in `group_vars/all.yml` (or role defaults)
2. Ensure tasks are idempotent by default
3. Add `enable_upgrades` check if upgrades are supported
4. Include health checks in post-deployment verification
5. Update UPGRADES.md with any breaking changes or special procedures

---

For details on role expectations and principles, see:
- [AGENTS.md](../AGENTS.md) — Project guardrails and governance
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — System design
- [docs/SETUP.md](../docs/SETUP.md) — Operational guide
