# AGENTS.md — Mac Mini Local LLM Server Provisioning (Ansible)

This repository provisions a **dedicated Mac mini** as a **stable, reproducible local LLM host**.

It is designed for long-term maintenance: safe upgrades, explicit model management, and clear separation between **host provisioning (Ansible)** and **service deployment (Docker containers)**.

This file is the durable operating guide for contributors and AI agents working in this repo.

## 1) Project intent and non-goals

### Intent
- Turn a Mac mini into a **reliable “appliance-like” LLM server**.
- Ensure **repeatable provisioning** from a clean machine state.
- Prefer **idempotent, deterministic** automation: re-running playbooks should converge to the same state.
- Make upgrades **safe and controlled** (pin versions; explicit upgrade steps; preflight checks; backups where relevant).

### Non-goals
- This is **not** a general macOS workstation bootstrap.
- This is **not** a “try anything” playground. Changes must be deliberate and compatible with a stable host.
- We do **not** hide complexity behind magic: every system change should be traceable to a role/task.


## 2) High-level architecture

The Mac mini is a host that provides:
- Homebrew (package + dependency management)
- Ollama (model runtime)
- Docker Desktop (container runtime)
- OpenWebUI (served via Docker containers)

### Separation of concerns
- **Ansible (host-level):** installs and configures Homebrew, Ollama, Docker Desktop; manages files, users, services,
  directories, permissions, and host settings needed for a stable runtime.
- **Docker (service-level):** runs OpenWebUI and any other containerized services; configuration is managed via
  Compose files and env files committed to this repo.
- **Models (Ollama-level):** declared explicitly in repo config; pulled/updated by Ansible in a controlled, reproducible way.

This separation is enforced so the host stays stable while services evolve safely.


## 3) Repository conventions

### Suggested layout (preferred)
- `playbooks/`
  - `site.yml` (entrypoint)
- `roles/`
  - `homebrew/`
  - `ollama/`
  - `docker_desktop/`
  - `openwebui/`
  - `models/`
  - `common/` (shared defaults, filesystem layout, assertions)
- `group_vars/`
  - `all.yml` (global defaults)
  - `macmini.yml` (host-specific overrides; keep minimal)
- `files/` and `templates/` (role-specific, scoped under each role when possible)
- `compose/`
  - `openwebui/compose.yml`
  - `openwebui/.env.example` (never commit secrets)
- `docs/`
  - design notes, upgrade runbooks, troubleshooting
- `Makefile` (optional): common commands (lint, check, dry-run)

If the current repo differs, refactor toward this structure over time while preserving functionality.


## 4) Operating principles (hard requirements)

### Idempotency (must)
All tasks must be safe to run repeatedly. Concretely:
- Prefer Ansible modules over raw shell commands.
- If shell is unavoidable, use `creates:`, `removes:`, or explicit checks to avoid repeated changes.
- Use `changed_when:` and `failed_when:` responsibly.
- Never “blindly overwrite” config without cause; use templates and compare-based updates.
- Tasks should be deterministic: no random paths, no “latest” without pinning, no interactive prompts.

### Version pinning (must)
We pin versions at the appropriate layer:
- **Homebrew packages:** pin formula versions where feasible; otherwise record and control upgrade cadence.
- **Ollama:** install a known version or verified channel; upgrades are explicit.
- **Docker Desktop:** install a known version; upgrades are explicit.
- **OpenWebUI container image:** pin an image tag (or digest if you want maximum reproducibility).

If you propose “always latest”, you must also propose a safety plan (rollback path, compatibility checks, tested matrix).

### Safe upgrades (must)
Upgrades must:
- Be explicit (a variable or an “upgrade” playbook path)
- Include preflight checks
- Avoid breaking a working system
- Provide a rollback plan (or at least documented recovery)

### Observability and troubleshooting (should)
- After provisioning, we should be able to verify service health quickly (CLI checks).
- Keep logs accessible (Docker logs, app logs).
- Prefer predictable file locations and clear documentation.


## 5) Host provisioning boundaries

### Homebrew responsibilities
- Install Homebrew (detect existing installation; do not clobber).
- Ensure brew is available in the environment used by Ansible.
- Install required packages (explicit list).
- Avoid “brew upgrade” by default; upgrades must be opt-in.

### Ollama responsibilities
- Install Ollama.
- Ensure the Ollama service is running (launchd / service integration as appropriate).
- Ensure a stable data directory exists and is documented (models can be large).
- Provide a “health check” task: confirm the API is reachable locally.

### Docker Desktop responsibilities
- Install Docker Desktop (pinned version).
- Ensure Docker is running (or clearly instruct the operator if manual start is required by macOS security UX).
- Confirm `docker` CLI works for the user running Ansible (or document the required user context).

### OpenWebUI responsibilities (container-level)
- Deploy via Docker Compose from `compose/openwebui/compose.yml`.
- All environment configuration is in `.env` (template example committed; secrets excluded).
- Prefer named volumes or explicit host-mapped directories (document where data lives).
- Validate container health post-deploy.


## 6) Model declaration and management (must be explicit)

### Model declaration file
Models must be declared in a committed config file (single source of truth), not sprinkled across tasks.

Preferred: `group_vars/all.yml` (or a dedicated file in `vars/`), e.g.:
- `ollama_models:`
  - `name: llama3.1:8b`
    `state: present`
  - `name: nomic-embed-text`
    `state: present`

Rules:
- Every model entry must include a **fully qualified name** as used by `ollama pull`.
- Model additions/removals must be explicit PR changes.
- Default behavior: ensure declared models are **present**.
- Optional behavior (controlled by a variable): prune unmanaged models (off by default).

### Model management behavior
- Pulling models is idempotent: if present, do not repull unless explicitly requested.
- Provide an explicit “refresh models” mode (e.g. variable `ollama_models_refresh=true`) that repulls.
- Provide a clear “prune unmanaged models” mode (e.g. `ollama_models_prune=true`) that removes models not declared.
  This is dangerous; keep default `false`.

### Reproducibility note
Model tags can move. If you require strict reproducibility, prefer:
- immutable identifiers (if the ecosystem supports them), or
- periodically “lock” versions/tags in a release process and test compatibility.


## 7) Execution modes and safety switches

The playbook should support distinct, predictable modes:
- **Default:** provision host + deploy services + ensure models present (safe, no upgrades, no pruning)
- **Upgrade mode:** opt-in upgrades for brew packages / Docker Desktop / Ollama / container images
- **Model maintenance mode:** refresh / prune models only when requested

Use variables (documented, with defaults) rather than branching ad-hoc logic.

Example variable conventions:
- `enable_upgrades: false`
- `ollama_models_refresh: false`
- `ollama_models_prune: false`
- `openwebui_image_tag: "pinned-tag-here"`
- `docker_desktop_version: "x.y.z"`
- `ollama_version: "x.y.z"`


## 8) Testing, validation, and “definition of done”

### Local checks (preferred)
- `ansible-lint` passes
- `yamllint` passes (if used)
- A “check mode” run (`--check`) should be mostly clean (some tasks may require exceptions; document them)

### Post-run health checks (must)
After a successful run, include verification tasks (or a separate `verify.yml`) that confirm:
- brew is installed and accessible
- Ollama is running and responds (API or CLI)
- Docker is running and can list containers
- OpenWebUI container is up (health or port check)
- Declared models exist (`ollama list` contains them)

These checks should be **fast** and clearly report failures.


## 9) Security and secrets

- Never commit secrets (API keys, tokens, passwords) to the repo.
- Provide `.env.example` and document required variables.
- Prefer local-only bindings by default (listen on localhost unless explicitly configured).
- Document firewall/network expectations.
- If remote access is desired, require explicit enablement and document authentication requirements.


## 10) Data locations and persistence

We must document where state lives:
- Ollama models directory (large; plan storage)
- Docker volumes / bind mounts for OpenWebUI
- Any configuration written by roles

Prefer:
- One root data directory (configurable), e.g. `/opt/local-llm` or similar.
- Clear ownership and permissions (avoid brittle “works only for one user” assumptions).


## 11) Contribution workflow

### Change discipline
- Small, reviewable changes.
- Each change should answer: “What does this alter on the host?” and “Is it safe to re-run?”
- Prefer adding verification steps when introducing new behavior.

### Role ownership
- Keep responsibilities narrow:
  - `homebrew` does brew only
  - `ollama` does Ollama only
  - `docker_desktop` does Docker Desktop only
  - `openwebui` does container config/deploy only
  - `models` does model reconciliation only

### Documentation
- Any non-obvious behavior gets documented in `docs/` and/or role README sections.


## 12) Guidance for AI agents (OpenCode + local LLM)

AI agents working in this repo must follow these rules:
- Do not introduce “implicit latest” upgrades.
- Do not collapse roles into one big playbook; preserve separation of concerns.
- Prefer Ansible modules; avoid raw shell unless necessary.
- When adding a dependency, add:
  - the pinned version (or documented rationale if pinning is impossible)
  - a verification step
  - documentation of where state lives
- When adding a model:
  - update the declared model list (single source of truth)
  - ensure tasks remain idempotent and safe by default
- If a task touches macOS security UX (permissions, privacy prompts), document operator actions clearly.

When uncertain, choose the safest option (no upgrades, no pruning, no destructive changes by default).


## 13) Known macOS constraints (acknowledge reality)

macOS provisioning may require manual steps due to OS security prompts (e.g., first run of Docker Desktop).
The playbooks should:
- detect and report when manual intervention is required
- stop safely with actionable guidance
- never loop or “force” changes that require interactive approval


## 14) Release and upgrade policy (recommended)

We use a simple policy:
- “Provisioning” is stable and conservative.
- Upgrades happen intentionally:
  - update pinned versions
  - run verification
  - record results (a changelog entry or release note)
- Keep an `UPGRADES.md` runbook describing the upgrade procedure and rollback considerations.


---

## Appendix: Glossary

- **Idempotent:** running automation repeatedly produces the same end state without unintended changes.
- **Pinned version:** explicitly chosen version; upgrades require code changes.
- **Reconciliation:** ensuring declared state (models/services) matches actual state.