# Architecture Overview

This document describes the design and structure of the local-llm-server provisioning system.

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│  Control Node (your workstation)                            │
│  - Ansible playbooks and roles                              │
│  - Inventory and configuration                              │
│  - Orchestration                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                    SSH/API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  Managed Node: Mac mini (target host)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Homebrew                                           │   │
│  │  - Package management                              │   │
│  │  - Dependency resolution                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Ollama                                             │   │
│  │  - LLM model runtime                                │   │
│  │  - API (localhost:11434)                            │   │
│  │  - Model storage: {{ local_llm_data_dir }}/ollama   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Docker Desktop                                     │   │
│  │  - Container runtime                               │   │
│  │  - Docker Compose orchestration                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OpenWebUI (Docker Container)                       │   │
│  │  - Web interface                                    │   │
│  │  - API (localhost:3000)                             │   │
│  │  - Storage: {{ local_llm_data_dir }}/openwebui      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  State & Data: /opt/local-llm                       │   │
│  │  - Models                                           │   │
│  │  - Configuration                                    │   │
│  │  - Volumes / Mounts                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Provisioning Layers

### 1. **Host Provisioning (Ansible)**
Responsibilities:
- Install and configure Homebrew
- Install and manage Ollama
- Install and configure Docker Desktop
- Manage filesystem layout and permissions
- Health checks and service verification

Tools: Ansible roles and playbooks

### 2. **Service Deployment (Docker Compose)**
Responsibilities:
- Deploy OpenWebUI container
- Environment configuration (`.env` file)
- Volume and network setup
- Container lifecycle

Tools: Docker Compose (`compose/openwebui/compose.yml`)

### 3. **Model Management (Ollama)**
Responsibilities:
- Declare models (single source of truth in `group_vars/`)
- Pull and verify models present
- Optional: refresh or prune models

Tools: Ansible `models` role + Ollama CLI

## Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│ group_vars/all.yml                                          │
│ ├─ Global defaults                                          │
│ ├─ Version pinning                                          │
│ ├─ Safety modes (upgrades, refresh, prune)                  │
│ ├─ Execution configuration                                  │
│ └─ Declared models                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ inventory/                                                  │
│ ├─ Host definitions                                         │
│ ├─ Connection details                                       │
│ └─ Host variables (overrides)                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ playbooks/                                                  │
│ ├─ site.yml (main provisioning entrypoint)                  │
│ └─ verify.yml (read-only health checks)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ roles/                                                      │
│ ├─ common/ (shared setup, assertions)                       │
│ ├─ homebrew/ (package mgmt)                                 │
│ ├─ ollama/ (model runtime)                                  │
│ ├─ docker_desktop/ (container runtime)                      │
│ ├─ models/ (model reconciliation)                           │
│ └─ openwebui/ (service deployment)                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ compose/openwebui/                                          │
│ ├─ compose.yml (container orchestration)                    │
│ └─ .env.example (configuration template)                    │
└─────────────────────────────────────────────────────────────┘
```

## Idempotency by Design

All Ansible tasks follow idempotency principles:

1. **Detection before change** — check if state is already correct
2. **No re-execution unless needed** — use `creates:`, `removes:`, conditions
3. **Changed tracking** — explicit `changed_when:` clauses
4. **Determinism** — no random or "latest" by default

**Security Note:** For production deployments, avoid `curl | sh` patterns. Use a safer approach:
```yaml
- name: Download Ollama installer
  ansible.builtin.get_url:
    url: https://ollama.ai/install.sh
    dest: /tmp/ollama_install.sh
    mode: '0755'
    checksum: sha256:<expected-hash>  # Verify checksum from release
  args:
    creates: /tmp/ollama_install.sh

- name: Install Ollama (if not present)
  shell: /tmp/ollama_install.sh
  args:
    creates: /usr/local/bin/ollama
  when: ollama_version != "skip"
```

## Versioning and Upgrades

### Pinning Strategy

- **Homebrew:** Formula versions pinned in role defaults
- **Ollama:** Version pinned in `group_vars/all.yml`
- **Docker Desktop:** Version pinned in `group_vars/all.yml`
- **Container images:** Tag pinned in `group_vars/all.yml`
- **Models:** Names (tags) pinned in `group_vars/all.yml`

### Upgrade Process

1. Update version variables in configuration
2. Review compatibility and breaking changes
3. Run with `--check` first (dry-run)
4. Execute on non-critical test machine if available
5. Document any breaking changes or manual steps
6. Update UPGRADES.md runbook

### Safety by Default

- `enable_upgrades: false` — no automatic upgrades
- `ollama_models_refresh: false` — no re-pulling
- `ollama_models_prune: false` — no destructive removal
- Run playbook repeatedly without side effects

## Configuration Hierarchy

Variables are resolved in order of precedence (later definitions override earlier ones):

1. Role defaults (`roles/<role>/defaults/main.yml`) — lowest precedence
2. Global defaults (`group_vars/all.yml`)
3. Group variables (`group_vars/<group>.yml`)
4. Host-specific variables (`host_vars/<hostname>.yml`) — not used initially
5. Command-line extra variables (`-e`) — highest precedence

See [Ansible variable precedence documentation](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) for the complete precedence order.

## Data Persistence

State lives in a configurable data directory:

```
/opt/local-llm/
├── ollama/
│   └── models/          # Large; can move to separate volume
├── openwebui/
│   ├── db/              # WebUI database
│   ├── cache/           # Cache files
│   └── config/          # Configuration
└── config/              # Shared configuration
```

All paths inherit from `local_llm_data_dir` variable (default: `/opt/local-llm`).

## Health Checks

Post-provisioning verification tasks confirm:

1. **Connectivity** — SSH and basic Ansible setup
2. **Homebrew** — accessible and functional
3. **Ollama** — running and API responsive
4. **Docker** — running and can list containers
5. **OpenWebUI** — container up and port responding
6. **Models** — declared models exist (`ollama list`)

These checks are fast and safe to run repeatedly.

## Security Posture

- **Localhost-only by default** — no remote exposure
- **No secrets in repo** — `.env` and credentials excluded
- **SSH key-based auth** — passwords not supported
- **Sudo with caution** — minimize elevated privileges
- **Read-only where possible** — verify tasks don't mutate state

Enable remote access only after deliberate configuration:
- Update networking bindings in `.env` or role config
- Document authentication requirements
- Review firewall rules

## Future Extensions

This scaffold supports:

- Additional models (declare in `ollama_models`)
- Additional containers (add to `compose/` and `roles/`)
- Role upgrades and refactoring (maintain separation of concerns)
- Custom health checks and monitoring
- Backup and restore procedures
- Multi-host deployments (add to inventory)

---

For detailed requirements and principles, see [AGENTS.md](../AGENTS.md).
