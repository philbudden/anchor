# Local LLM Server

This repository provisions a **dedicated Mac mini** as a **stable, reproducible local LLM host**.

It is designed for long-term maintenance: safe upgrades, explicit model management, and clear separation between **host provisioning (Ansible)** and **service deployment (Docker containers)**.

## Quick Start

1. **Review the architecture:**
   - Read [AGENTS.md](AGENTS.md) for project principles and guardrails
   - Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design

2. **Set up your environment:**
   - Install requirements: `pip install -r requirements.txt`
   - Configure target host in `inventory/hosts.yml`
   - Review defaults in `group_vars/all.yml`

3. **Create data directory on target Mac:**
   ```bash
   # SSH to the Mac mini and create the directory (default: /opt/local-llm)
   ssh user@macmini "sudo mkdir -p /opt/local-llm && sudo chown $(whoami) /opt/local-llm"
   ```
   Or customize the path by setting `local_llm_data_dir` in your inventory.

4. **Install prerequisites (fresh Mac only):**
   ```bash
   ansible-playbook playbooks/preflight.yml
   ```

5. **Verify connectivity:**
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

6. **Provision the host:**
   ```bash
   ansible-playbook playbooks/site.yml --check  # Dry-run first
   ansible-playbook playbooks/site.yml           # Apply
   ```

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

## Project Structure

```
.
├── AGENTS.md                    # Project principles and guardrails
├── README.md                    # This file
├── ansible.cfg                  # Ansible configuration
├── requirements.txt             # Python/Ansible dependencies
├── Makefile                     # Helper commands (lint, check, verify, provision)
│
├── inventory/
│   └── hosts.yml               # Target host definitions
│
├── group_vars/
│   ├── all.yml                 # Global defaults and configuration
│   └── macmini.yml             # Host-specific overrides (minimal)
│
├── playbooks/
│   ├── site.yml                # Main provisioning entrypoint
│   └── verify.yml              # Connectivity and health checks (read-only)
│
├── roles/
│   ├── common/                 # Shared setup and assertions
│   ├── homebrew/               # Homebrew installation
│   ├── ollama/                 # Ollama LLM runtime
│   ├── docker_desktop/         # Docker Desktop
│   ├── models/                 # Model reconciliation
│   ├── openwebui/              # OpenWebUI deployment
│   └── README.md               # Role documentation
│
├── compose/
│   └── openwebui/
│       └── .env.example        # Environment template (no secrets)
│                               # (compose.yml generated from template)
│
├── docs/
│   ├── SETUP.md                # Setup and operational guide
│   ├── ARCHITECTURE.md         # System design and components
│   └── UPGRADES.md             # Upgrade procedures and policy
│
├── .gitignore                  # Excludes secrets and cache
├── .yamllint                   # YAML linting configuration
└── .ansible-lint               # Ansible linting configuration
```

## Key Features

✅ **Idempotent** — Run playbooks repeatedly; always converges safely  
✅ **Version-pinned** — All components have explicit versions; no "latest" by default  
✅ **Safe by default** — No upgrades, no destructive actions unless explicitly enabled  
✅ **Clear separation** — Host provisioning, service deployment, and model management are independent  
✅ **GitOps-ready** — All state declared in version control; reproducible from git checkout  
✅ **Observable** — Health checks and verification tasks included  
✅ **Maintainable** — One role per subsystem; clear responsibilities  

## Configuration

All configuration is centralized in version control:

- **Global defaults:** `group_vars/all.yml`
- **Host overrides:** `group_vars/macmini.yml` (keep minimal)
- **Target host:** `inventory/hosts.yml`
- **Execution modes:** Variables in `group_vars/all.yml`
  - `enable_upgrades` — Opt-in upgrades for Homebrew, Docker, Ollama
  - `ollama_models_refresh` — Repull all declared models
  - `ollama_models_prune` — Remove unmanaged models (dangerous)
- **Models:** Declared in `ollama_models` list (single source of truth)

See [docs/SETUP.md](docs/SETUP.md) for configuration details.

## Commands

Use the Makefile for common tasks:

```bash
make help              # Show all available commands

# Testing (run before committing)
make test              # Run all validation checks (fast)
make test-all          # Run all tests including linting
make lint              # Run ansible-lint and yamllint
make syntax-check      # Check Ansible playbook syntax
make validate          # Run custom validation scripts

# Provisioning
make verify            # Test connectivity to target host
make check             # Dry-run provisioning (--check mode)
make provision         # Run provisioning (no upgrades)
make provision-upgrade # Run provisioning with upgrades enabled

# Maintenance
make clean             # Clean Ansible cache
```

Or run playbooks directly:

```bash
ansible-playbook playbooks/verify.yml
ansible-playbook playbooks/site.yml --check
ansible-playbook playbooks/site.yml -e enable_upgrades=true
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Design Principles

This project follows strict principles (see [AGENTS.md](AGENTS.md)):

1. **Idempotency (must):** All tasks safe to run repeatedly.
2. **Version pinning (must):** No implicit "latest" upgrades.
3. **Safe upgrades (must):** Explicit opt-in; include rollback procedures.
4. **Separation of concerns (must):** Each role has a clear, narrow responsibility.
5. **Explicit configuration (must):** All state declared in version control.
6. **Observability (should):** Health checks and clear error messages.

## Upgrade Policy

Upgrades are **intentional and controlled**:

1. Update version variable in `group_vars/all.yml`
2. Test in `--check` mode first
3. Apply with `enable_upgrades=true`
4. Verify with `playbooks/verify.yml`
5. Document changes and any breaking behavior

See [docs/UPGRADES.md](docs/UPGRADES.md) for detailed procedures per component.

## Security

- **Localhost-only by default** — No remote exposure without explicit configuration
- **No secrets in repo** — `.env` files and credentials are gitignored
- **SSH key-based auth** — Passwords not supported
- **Minimal elevation** — Use sudo sparingly; document why

## Supported Environments

- **Target:** macOS 12+, Mac mini or equivalent
- **Control node:** macOS, Linux, or WSL with Ansible 2.13+
- **SSH:** SSH keys required; password auth not supported

## Documentation

- [AGENTS.md](AGENTS.md) — Project intent, guardrails, and guidance for contributors
- [TESTING.md](TESTING.md) — Testing strategy, CI workflows, and validation details
- [docs/SETUP.md](docs/SETUP.md) — Setup and operational procedures
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design and component overview
- [docs/UPGRADES.md](docs/UPGRADES.md) — Upgrade procedures and rollback plans
- [roles/README.md](roles/README.md) — Role responsibilities and structure

## Contributing

Follow the principles in [AGENTS.md](AGENTS.md):

- Keep changes small and reviewable
- Maintain role separation
- Pin all versions
- Include verification steps
- Update documentation

## License

See [LICENSE](LICENSE) for details.

