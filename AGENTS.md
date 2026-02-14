This repository provisions a **dedicated Mac mini** as a **stable, reproducible local LLM host**.

It is designed for long-term maintenance: safe upgrades, explicit model management, and clear separation between **host provisioning (Ansible)** and **service deployment (Docker containers)**.

This file is the durable operating guide for contributors and AI agents working in this repo.

---
## 1) Project intent and non-goals

### Intent

- Turn a Mac mini into a **reliable “appliance-like” LLM server**.
- Ensure **repeatable provisioning** from a clean machine state.
- Prefer **idempotent, deterministic** automation: re-running playbooks should converge to the same state.
- Make upgrades **safe and controlled** (pin versions; explicit upgrade steps; preflight checks; backups where relevant).
- Maintain a **layered testing strategy** that provides fast feedback while minimizing reliance on macOS runners.

### Non-goals

- This is **not** a general macOS workstation bootstrap.
- This is **not** a “try anything” playground. Changes must be deliberate and compatible with a stable host.
- We do **not** hide complexity behind magic: every system change should be traceable to a role/task.
- We do **not** introduce heavy testing frameworks or architectural complexity beyond what is necessary for safety and reproducibility.

---
## 2) High-level architecture

The Mac mini is a host that provides:
- Homebrew (package + dependency management)
- Ollama (model runtime)
- Docker Desktop (container runtime)
- OpenWebUI (served via Docker containers)

### Separation of concerns

- **Ansible (host-level):** installs and configures Homebrew, Ollama, Docker Desktop; manages files, users, services, directories, permissions, and host settings needed for a stable runtime.
- **Docker (service-level):** runs OpenWebUI and any other containerized services; configuration is managed via Compose files and env files committed to this repo.
- **Models (Ollama-level):** declared explicitly in repo config; pulled/updated by Ansible in a controlled, reproducible way.

This separation is enforced so the host stays stable while services evolve safely.

---
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
    - `openwebui/.env.example` (never commit secrets)
    - Note: `compose.yml` is generated from templates on target host to ensure consistency with variables
- `docs/`
    - design notes, upgrade runbooks, troubleshooting
- `Makefile` (optional): common commands (lint, check, dry-run)

If the current repo differs, refactor toward this structure over time while preserving functionality.

---
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
- **OpenWebUI container image:** pin an image tag (or digest if maximum reproducibility is required).

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

---
## 5) Host provisioning boundaries

### Homebrew responsibilities

- Install Homebrew (detect existing installation; do not clobber).
- Ensure brew is available in the environment used by Ansible.
- Install required packages (explicit list).
- Avoid `brew upgrade` by default; upgrades must be opt-in.

### Ollama responsibilities

- Install Ollama.
- Ensure the Ollama service is running (launchd / service integration as appropriate).
- Ensure a stable data directory exists and is documented (models can be large).
- Provide a health check task: confirm the API is reachable locally.

### Docker Desktop responsibilities

- Install Docker Desktop (pinned version).
- Ensure Docker is running (or clearly instruct the operator if manual start is required by macOS security UX).
- Confirm `docker` CLI works for the user running Ansible (or document the required user context).

### OpenWebUI responsibilities (container-level)

- Deploy via Docker Compose from `compose/openwebui/compose.yml`.
- All environment configuration is in `.env` (template example committed; secrets excluded).
- Prefer named volumes or explicit host-mapped directories (document where data lives).
- Validate container health post-deploy.

---
## 6) Model declaration and management (must be explicit)

### Model declaration file

Models must be declared in a committed config file (single source of truth), not sprinkled across tasks.

Preferred location: `group_vars/all.yml` (or a dedicated vars file), for example:

```yaml
ollama_models:
  - name: llama3.1:8b
    state: present
  - name: nomic-embed-text
    state: present
```

Rules:
- Every model entry must include a **fully qualified name** as used by `ollama pull`.
- Model additions/removals must be explicit PR changes.
- Default behavior: ensure declared models are **present**.
- Optional behavior (controlled by a variable): prune unmanaged models (off by default).

### Model management behavior

- Pulling models is idempotent: if present, do not repull unless explicitly requested.
- Provide an explicit “refresh models” mode (e.g. `ollama_models_refresh: true`) that repulls.
- Provide a clear “prune unmanaged models” mode (e.g. `ollama_models_prune: true`) that removes models not declared.  
    This is dangerous; keep default `false`.

### Reproducibility note

Model tags can move. If strict reproducibility is required, prefer:
- immutable identifiers (if supported), or
- periodically “lock” versions/tags in a controlled release process.

---
## 7) Execution modes and safety switches

The playbook should support distinct, predictable modes:
- **Default:** provision host + deploy services + ensure models present (safe, no upgrades, no pruning)
- **Upgrade mode:** opt-in upgrades for brew packages / Docker Desktop / Ollama / container images
- **Model maintenance mode:** refresh / prune models only when requested

Use documented variables (with defaults) rather than branching ad-hoc logic.

Example variable conventions:
```yaml
enable_upgrades: false
ollama_models_refresh: false
ollama_models_prune: false
openwebui_image_tag: "pinned-tag"
docker_desktop_version: "x.y.z"
ollama_version: "x.y.z"
```

---
## 8) Layered testing and validation philosophy (first-class constraint)

Testing is a core design principle. All changes must respect the layered validation model:
**lint → structural validation → limited integration → full macOS integration**

### 8.1 What must pass in CI before merging (mandatory)

All pull requests must pass Linux-based CI checks:
- YAML formatting validation
- `ansible-lint`
- `ansible-playbook --syntax-check`
- Structural validation (role layout, required files, task organization)
- Static validation of declared variables and model definitions

CI must:
- Run primarily on Linux runners
- Fail fast on lint or syntax errors
- Avoid macOS runners by default

If CI fails, the change is not merge-ready.

### 8.2 What is validated on Linux

Linux CI validates:
- YAML correctness and formatting
- Ansible syntax and task structure
- Role boundaries and organization
- Variable rendering and templating correctness
- Model declaration structure
- Idempotency patterns (e.g., misuse of `shell` without guards)

Linux CI does **not** validate:
- macOS-specific runtime behavior
- launchd integration
- Docker Desktop UX/security prompts
- Actual Ollama model pulls

The purpose of Linux CI is fast feedback and structural safety.

### 8.3 What requires macOS

Only macOS can validate:
- Real Homebrew installation behavior
- Ollama service behavior under launchd
- Docker Desktop installation and startup semantics
- Full end-to-end provisioning

Full macOS VM tests are a **higher-level integration layer**, not a per-commit requirement.

They may be:
- Manual
- Scheduled
- Explicitly triggered

They are slower and intentionally limited in frequency.

---
## 9) Designing for testability (required mindset)

When adding or modifying tasks:
- Separate **decision logic** from **execution logic**.
- Guard macOS-specific tasks explicitly (e.g., `when: ansible_system == 'Darwin'`).
- Keep role responsibilities narrow and isolated.
- Make model lists and configuration declarative.
- Avoid embedding logic directly in shell commands.

Ask:
- Can this be validated in Linux CI without macOS?
- Is this idempotent?
- Is this upgrade-safe?
- Does this change require additional verification tasks?

If adding non-idempotent behavior is unavoidable, document why and constrain it carefully.

---
## 10) Post-run health checks (must)

After a successful run, verification tasks (or a `verify.yml`) must confirm:
- brew is installed and accessible
- Ollama is running and responds (API or CLI)
- Docker CLI works
- OpenWebUI container is up
- Declared models exist (`ollama list` includes them)

These checks must be fast and clearly report failures.

---
## 11) Security and secrets

- Never commit secrets (API keys, tokens, passwords).
- Provide `.env.example` and document required variables.
- Prefer local-only bindings by default.
- Document firewall/network expectations.
- Remote access must require explicit configuration and documented authentication.

---
## 12) Data locations and persistence

We must document where state lives:
- Ollama models directory (large; plan storage)
- Docker volumes / bind mounts for OpenWebUI
- Any configuration written by roles

Prefer:
- One configurable root data directory
- Clear ownership and permissions
- No hidden state

---
## 13) Contribution workflow

### Change discipline

- Small, reviewable changes.
- Each change must answer:
    - What does this alter on the host?
    - Is it safe to re-run?
    - Does it respect CI and layered testing?

### Role ownership

Keep responsibilities narrow:
- `homebrew` → brew only
- `ollama` → Ollama only
- `docker_desktop` → Docker Desktop only
- `openwebui` → container config/deploy only
- `models` → model reconciliation only

### Documentation

Any non-obvious behavior must be documented in `docs/` or role README sections.

---
## 14) Guidance for AI agents

AI agents must:
- Respect version pinning.
- Avoid implicit upgrades.
- Preserve separation of concerns.
- Prefer Ansible modules.
- Maintain idempotency.
- Ensure changes pass Linux CI validation.
- Add verification steps when introducing new behavior.
- Update the declared model list explicitly when adding models.

When uncertain, choose the safest option (no upgrades, no pruning, no destructive changes by default).

---
## 15) Known macOS constraints

macOS provisioning may require manual steps due to OS security prompts (e.g., first run of Docker Desktop).

Playbooks should:
- Detect and report when manual intervention is required.
- Stop safely with actionable guidance.
- Never force changes that require interactive approval.

---
## 16) Release and upgrade policy

Provisioning is conservative and stable.

Upgrades happen intentionally:
- Update pinned versions.
- Run Linux CI.
- Perform macOS integration validation.
- Record outcomes in changelog or upgrade notes.

Maintain an `UPGRADES.md` runbook describing upgrade and rollback considerations.

---
## Appendix: Glossary

- **Idempotent:** running automation repeatedly produces the same end state without unintended changes.
- **Pinned version:** explicitly chosen version; upgrades require code changes.
- **Reconciliation:** ensuring declared state matches actual state.
- **Layered testing:** staged validation from static checks to full integration.
