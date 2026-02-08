-# Setup and Operational Guide

This document describes how to set up the Ansible provisioning environment and connect to the target Mac mini.

## Prerequisites

### Control Node (your workstation)
You need Ansible installed and available:

```bash
# macOS
brew install ansible

# or via pip (if using virtualenv)
python3 -m venv venv
source venv/bin/activate
pip install ansible yamllint ansible-lint
```

Verify installation:
```bash
ansible --version
```

### Target Mac mini (managed node)

1. **SSH Access**
   - Ensure SSH is enabled (`System Preferences > Sharing > Remote Login`)
   - Create or provision an SSH user account (e.g., `automation`)
   - Ensure the control node SSH key is authorized (add to `.ssh/authorized_keys`)

2. **Data Directory**
   - Create the data directory with appropriate permissions:
     ```bash
     sudo mkdir -p /opt/local-llm
     sudo chown -R $(whoami):staff /opt/local-llm
     chmod 755 /opt/local-llm
     ```
   - Or customize the path by overriding `local_llm_data_dir` in inventory or group_vars

3. **Sudo (if required)**
   - Some tasks may require sudo; ensure the automation user can run sudo commands
   - Test: `ssh automation@macmini-ip sudo -n true`

## Configuration

### Step 1: Update Inventory

Edit `inventory/hosts.yml` and configure your target host:

```yaml
macmini_primary:
  ansible_host: <IP or hostname>      # e.g., 192.168.1.100 or macmini.local
  ansible_user: <ssh_user>            # e.g., automation
  # Uncomment if needed:
  # ansible_port: 2222
  # ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

### Step 2: Configure Global Defaults

Edit `group_vars/all.yml` and adjust:

- `local_llm_data_dir`: Root directory for models and state
- `ollama_version`, `docker_desktop_version`, `openwebui_image_tag`: Pinned versions
- `enable_upgrades`, `ollama_models_refresh`, `ollama_models_prune`: Safety modes

Declare models if needed:

```yaml
ollama_models:
  - name: llama3.1:8b
    state: present
  - name: nomic-embed-text
    state: present
```

### Step 3: Test Connectivity

Verify SSH connectivity and environment detection:

```bash
ansible-playbook playbooks/verify.yml
```

This playbook is **read-only** and safe to run repeatedly. It gathers facts and validates configuration assumptions.

## Provisioning

Once connectivity is verified, the main provisioning playbook is ready:

```bash
# Default run (no upgrades, safe)
ansible-playbook playbooks/site.yml

# Dry-run (check mode; no changes applied)
ansible-playbook playbooks/site.yml --check

# With upgrades enabled (only when intentional)
ansible-playbook playbooks/site.yml -e enable_upgrades=true

# Run only specific role
ansible-playbook playbooks/site.yml --tags ollama

# Run only verification posts
ansible-playbook playbooks/site.yml --tags verify
```

## Environment Files

### OpenWebUI .env

Copy `.env.example` to `.env` and configure:

```bash
cp compose/openwebui/.env.example compose/openwebui/.env
```

Edit `compose/openwebui/.env` (never commit this file):

```bash
OPENWEBUI_HOST=127.0.0.1
OPENWEBUI_PORT=3000
OLLAMA_API_BASE_URL=http://127.0.0.1:11434
```

## Safety Principles

All automation follows these principles (see AGENTS.md):

1. **Idempotency:** Running playbooks repeatedly converges to the same state safely.
2. **Explicit Configuration:** No "latest" by default; all versions are pinned.
3. **No Destructive Changes:** Default mode never upgrades, prunes, or removes without explicit enablement.
4. **Clear Separation:** Host provisioning (Ansible) is separate from service deployment (Docker).
5. **Observability:** Health checks and verification tasks run post-provisioning.

## Troubleshooting

### SSH Connection Refused
- Verify SSH is enabled on the Mac mini
- Verify username and IP/hostname in inventory
- Test manually: `ssh automation@macmini-ip -vvv`

### Permission Denied (sudo)
- Ensure the automation user is in sudoers: `sudo visudo`
- Add: `automation ALL=(ALL) NOPASSWD: ALL` (or restrict commands as needed)

### Data Directory Errors
- Create `/opt/local-llm` manually if not present
- Ensure proper ownership: `sudo chown -R $(whoami):staff /opt/local-llm`

### Fact Cache Issues
- Clear fact cache: `rm -rf /tmp/ansible_facts_cache`
- Re-run verify playbook

## Next Steps

1. Ensure inventory is configured
2. Run `playbooks/verify.yml` to validate connectivity
3. Review `group_vars/all.yml` for any customizations
4. Refer to individual role documentation in `docs/` for specific features

## References

- [AGENTS.md](../AGENTS.md) — Project architecture and guardrails
- [Ansible Documentation](https://docs.ansible.com/)
- [Ollama Documentation](https://ollama.ai/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
