# Deployment Guide

Complete guide for deploying the local LLM server on a Mac mini.

## Prerequisites

### Control Machine (Your laptop/workstation)

- Linux, macOS, or WSL
- Python 3.9+
- Ansible 2.17+
- Git
- SSH client

### Target Mac mini

- macOS 12.0 or newer (Monterey, Ventura, Sonoma recommended)
- At least 16GB RAM (32GB+ recommended for larger models)
- At least 100GB free disk space (models can be 5-50GB each)
- Network connectivity
- SSH access enabled
- User account with sudo privileges

## Step-by-Step Deployment

### 1. Prepare Control Machine

```bash
# Clone repository
git clone <repository-url>
cd local-llm-server

# Install Python dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Verify Ansible installation
ansible --version  # Should show 2.17 or higher
```

### 2. Enable SSH on Mac mini

On the Mac mini:

1. Open **System Settings** > **General** > **Sharing**
2. Enable **Remote Login**
3. Add your user to the allowed users list
4. Note the Mac mini's IP address or hostname

### 3. Configure SSH Keys (Recommended)

From your control machine:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to Mac mini
ssh-copy-id username@mac-mini-ip

# Test connection
ssh username@mac-mini-ip "echo Connection successful"
```

### 4. Configure Sudo Access (Required)

Ansible requires sudo privileges to install system components and create directories.

**Choose one of the following options:**

#### Option A: Passwordless Sudo (Recommended for Automation)

On the Mac mini:

```bash
# SSH to Mac mini
ssh username@mac-mini-ip

# Edit sudoers file (opens in safe mode)
sudo visudo

# Add this line at the end (replace 'username' with your actual username):
username ALL=(ALL) NOPASSWD: ALL

# Save and exit (Ctrl+X, then Y, then Enter in nano)
```

**Verification:**
```bash
# Test passwordless sudo
sudo echo "Sudo works without password"
# Should not prompt for password
```

#### Option B: Provide Password at Runtime

If you prefer not to use passwordless sudo, you can provide the password when running playbooks:

```bash
ansible-playbook playbooks/site.yml --ask-become-pass
# You'll be prompted for sudo password
```

**Note**: This requires interactive input and is less suitable for automation.

#### Option C: Use Ansible Vault (Production Recommended)

For production environments, store the encrypted sudo password:

```bash
# Create encrypted vault file
ansible-vault create inventory/group_vars/all/vault.yml

# Add this content in the editor that opens:
---
ansible_become_password: your_sudo_password_here

# Save and exit

# Run playbooks with vault password:
ansible-playbook playbooks/site.yml --ask-vault-pass
```

**Security Note**: Option A (passwordless sudo) is convenient for test/development environments. For production Mac minis, use Option C with Ansible Vault to maintain security while enabling automation.

### 5. Configure Inventory

Edit `inventory/hosts.yml`:

```yaml
all:
  children:
    macmini:
      hosts:
        macmini_primary:
          ansible_host: 192.168.1.100  # Your Mac mini IP
          ansible_user: yourusername    # Your Mac user
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519  # Your SSH key
```

### 5. Verify Connectivity

```bash
ansible-playbook playbooks/verify.yml
```

Expected output:
```
TASK [Verify SSH connectivity with ping] *****
ok: [macmini_primary]

TASK [Display target host facts] *************
ok: [macmini_primary] => {
    "msg": "Hostname: mac-mini\nOS: Darwin / macOS 14.2\n..."
}
```

### 6. Run Preflight (First-Time Only)

This installs Xcode Command Line Tools (required for Homebrew):

```bash
ansible-playbook playbooks/preflight.yml
```

**Note**: If this triggers an interactive installation dialog on the Mac, accept it and re-run the playbook.

### 7. Review Configuration

Check `inventory/group_vars/all.yml` and verify:

- `local_llm_data_dir: /opt/local-llm` (sufficient disk space?)
- Model list matches your needs
- Version pins are acceptable

### 8. Dry-Run Provisioning

```bash
ansible-playbook playbooks/site.yml --check
```

Review the output. This shows what *would* change without making changes.

**Common check-mode warnings** (safe to ignore):
- "Could not find file" for templates/configs (not created yet)
- Skipped tasks that depend on previous tasks

### 9. Full Provisioning

```bash
ansible-playbook playbooks/site.yml
```

This will:
1. ✅ Create data directories
2. ✅ Install Homebrew
3. ✅ Install Ollama
4. ✅ Install Docker Desktop
5. ✅ Pull declared Ollama models (can take 30-60 minutes)
6. ✅ Deploy OpenWebUI container

**Expected duration**: 45-90 minutes (mostly model downloads)

**Progress monitoring**:
```bash
# In another terminal, SSH to Mac mini and watch
ssh mac-mini "tail -f /tmp/ollama-install.log"  # if exists
ssh mac-mini "ollama list"  # see models as they download
```

### 10. Verify Deployment

```bash
# Run verification playbook
ansible-playbook playbooks/verify.yml

# Check Ollama API
ssh mac-mini "curl -s http://127.0.0.1:11434/api/tags | head -20"

# Check OpenWebUI
ssh mac-mini "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000"
# Should return: 200

# List models
ssh mac-mini "ollama list"
```

### 11. Access OpenWebUI

From the Mac mini (or via SSH tunnel):

```bash
# Option 1: Direct access on Mac mini
open http://127.0.0.1:3000

# Option 2: SSH tunnel from control machine
ssh -L 3000:127.0.0.1:3000 username@mac-mini-ip
# Then open http://localhost:3000 on control machine
```

## Post-Deployment

### Initial OpenWebUI Setup

1. Open http://127.0.0.1:3000 (or via SSH tunnel)
2. Create admin account (first user is admin)
3. Verify Ollama connection in Settings > Connections
4. Select a model and test a prompt

### Validation Checklist

- [ ] Homebrew installed: `ssh mac-mini "brew --version"`
- [ ] Ollama running: `ssh mac-mini "brew services list | grep ollama"`
- [ ] Docker running: `ssh mac-mini "docker ps"`
- [ ] All 8 models pulled: `ssh mac-mini "ollama list | wc -l"` (should be 9 lines: header + 8 models)
- [ ] OpenWebUI accessible: `curl http://127.0.0.1:3000` (via SSH tunnel or on Mac)
- [ ] Can generate text via OpenWebUI

### Performance Tuning

**Model selection** (for limited RAM):
- For 16GB RAM: Use `7b`/`8b` models only
- For 32GB RAM: Can run `13b` models
- For 64GB+ RAM: Can run larger models

**Disk space monitoring**:
```bash
ssh mac-mini "du -sh /opt/local-llm/*"
```

## Troubleshooting

### Missing sudo password error

**Symptom**: Playbook fails with "Missing sudo password" or "privilege escalation required"

```
fatal: [macmini_primary]: FAILED! => {"changed": false, "msg": "Task failed: Missing sudo password"}
```

**Cause**: Ansible needs sudo privileges to create system directories and install packages.

**Solution**: Configure sudo access (see Step 4 above). Choose one:

1. **Quick fix for testing**: Run with `--ask-become-pass` flag:
   ```bash
   ansible-playbook playbooks/site.yml --check --ask-become-pass
   ```

2. **Permanent fix (recommended)**: Configure passwordless sudo on Mac mini:
   ```bash
   # On Mac mini:
   sudo visudo
   # Add: username ALL=(ALL) NOPASSWD: ALL
   ```

3. **Production fix**: Use Ansible Vault (see Step 4, Option C above)

### Preflight fails: Xcode tools not installing

**Symptom**: `xcode-select -p` fails after preflight

**Solution**:
```bash
# On Mac mini directly:
xcode-select --install
# Accept the dialog, wait for completion
# Re-run: ansible-playbook playbooks/preflight.yml
```

### Docker Desktop not starting

**Symptom**: `docker info` fails, "Cannot connect to Docker daemon"

**Solution**:
1. On Mac mini, open **Applications** > **Docker**
2. Accept security prompts
3. Wait for Docker to fully start (whale icon in menu bar)
4. Re-run: `ansible-playbook playbooks/site.yml --tags docker_desktop,openwebui`

### Ollama models not pulling

**Symptom**: Provisioning hangs on "Pull declared models"

**Solution**:
```bash
# SSH to Mac mini
ssh mac-mini

# Check Ollama is running
brew services list | grep ollama

# Manually test pull
ollama pull llama3.1:8b

# Check network/disk space
df -h /opt/local-llm
ping -c 3 ollama.com
```

### OpenWebUI shows "Ollama connection failed"

**Symptom**: Web UI loads but can't connect to Ollama

**Solution**:
```bash
# Check Ollama API responds
ssh mac-mini "curl http://127.0.0.1:11434/api/tags"

# Check Docker env file
ssh mac-mini "cat /opt/local-llm/compose/openwebui/.env | grep OLLAMA"

# Should show: OLLAMA_API_BASE_URL=http://127.0.0.1:11434

# Restart OpenWebUI
ssh mac-mini "cd /opt/local-llm/compose/openwebui && docker compose restart"
```

### Disk space issues

**Symptom**: "No space left on device"

**Solution**:
```bash
# Check usage
ssh mac-mini "du -sh /opt/local-llm/*"

# Remove unused models
ssh mac-mini "ollama list"
ssh mac-mini "ollama rm model-name:tag"

# Clean Docker
ssh mac-mini "docker system prune -a"
```

## Upgrades

See [UPGRADES.md](UPGRADES.md) for detailed upgrade procedures.

Quick upgrade (all components):
```bash
# 1. Edit inventory/group_vars/all.yml and update version pins
# 2. Run with upgrades enabled
ansible-playbook playbooks/site.yml -e enable_upgrades=true
```

## Rollback

If provisioning fails or breaks existing setup:

### Homebrew rollback
```bash
ssh mac-mini "brew list --versions <package>"
ssh mac-mini "brew switch <package> <version>"
```

### Ollama rollback
```bash
ssh mac-mini "brew uninstall ollama"
ssh mac-mini "brew install ollama@<version>"
```

### Full reset (nuclear option)
```bash
# On Mac mini:
sudo rm -rf /opt/local-llm
brew uninstall ollama
brew uninstall --cask docker
rm -rf ~/.ollama

# Re-provision from scratch
ansible-playbook playbooks/site.yml
```

## Security Considerations

### Default configuration (safe)
- All services bind to 127.0.0.1 (localhost only)
- No remote access without SSH tunnel
- No authentication required (localhost trust model)

### Enabling remote access (advanced)

**⚠️ Security warning**: Remote access exposes services to your network.

1. Edit `inventory/group_vars/all.yml`:
   ```yaml
   ollama_api_host: "0.0.0.0"  # Listen on all interfaces
   openwebui_api_host: "0.0.0.0"
   ```

2. Re-run provisioning:
   ```bash
   ansible-playbook playbooks/site.yml --tags ollama,openwebui
   ```

3. Configure firewall on Mac mini
4. Enable authentication in OpenWebUI settings
5. Use HTTPS with reverse proxy (nginx/Caddy)

## Maintenance

### Weekly
- Monitor disk space: `du -sh /opt/local-llm`
- Check service health: `ansible-playbook playbooks/verify.yml`

### Monthly
- Update models: `ansible-playbook playbooks/site.yml -e ollama_models_refresh=true --tags models`
- Review Docker logs: `ssh mac-mini "docker compose -f /opt/local-llm/compose/openwebui/compose.yml logs --tail 100"`

### Quarterly
- Review and apply system upgrades (Ollama, Docker, OpenWebUI)
- Clean unused Docker images: `ssh mac-mini "docker system prune -a"`
- Backup configuration (already in git)

## Support

- **Issues**: Open GitHub issue with logs and error messages
- **Questions**: See [AGENTS.md](../AGENTS.md) for architecture
- **Testing**: See [TESTING.md](../TESTING.md) for validation approach

## Next Steps

After successful deployment:
1. Review [AGENTS.md](../AGENTS.md) to understand design principles
2. Explore OpenWebUI features and model capabilities
3. Set up monitoring/alerting if needed
4. Document any customizations in `group_vars/macmini.yml`
