# Quick Start Guide

Get your local LLM server running in minutes.

## Prerequisites

- Mac mini running macOS 12+
- SSH access to Mac mini
- Linux/macOS/WSL control machine
- Python 3.9+ and pip
- ~100GB free disk space on Mac mini

## 5-Minute Setup

### 1. Install Dependencies (Control Machine)

```bash
git clone <repository-url>
cd local-llm-server

pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

### 2. Configure Target Host

```bash
cp inventory.hosts.yml.example inventory/hosts.yml
nano inventory/hosts.yml  # Edit with your Mac mini details
```

Example:
```yaml
ansible_host: 192.168.1.100
ansible_user: your-username
ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

### 3. Configure Sudo (Required)

On your Mac mini, enable passwordless sudo for automation:

```bash
# SSH to Mac mini
ssh your-username@mac-mini-ip

# Edit sudoers file
sudo visudo

# Add this line (replace 'your-username'):
your-username ALL=(ALL) NOPASSWD: ALL

# Save and exit
```

**Alternative**: Use `--ask-become-pass` flag when running playbooks (prompted for sudo password each time).

### 4. Create Data Directory on Mac mini

```bash
# SSH to Mac mini and create the directory (default: /opt/local-llm)
ssh your-username@mac-mini-ip "sudo mkdir -p /opt/local-llm && sudo chown $(whoami) /opt/local-llm"
```

**Note**: Customize the path by setting `local_llm_data_dir` in `inventory/group_vars/all.yml` if needed.

### 5. Test Connection

```bash
ansible-playbook playbooks/verify.yml
```

Expected: ✅ SSH ping successful, data directory verified

### 6. Install Prerequisites on Mac mini

```bash
ansible-playbook playbooks/preflight.yml
```

Expected: Xcode CLI Tools installed (or already present)

### 7. Provision Everything

```bash
# Dry-run first (safe)
ansible-playbook playbooks/site.yml --check

# If dry-run looks good, provision for real
ansible-playbook playbooks/site.yml
```

**What to expect:**

**First run:**
- Homebrew, Ollama, and Docker Desktop will be installed
- **Playbook will fail** with instructions if Docker daemon is not running
- This is expected behavior (macOS security requires manual Docker launch)

**After Docker Desktop install fails:**
1. On the Mac mini, launch Docker Desktop (`/Applications/Docker.app`)
2. Accept macOS security prompts (first-time launch)
3. Wait for Docker whale icon in menu bar to be steady (not animating)
4. Re-run: `ansible-playbook playbooks/site.yml`

**Second run (after starting Docker):**
- Playbook skips already-completed steps (Homebrew, Ollama, Docker install)
- Verifies Docker daemon is running ✅
- Deploys OpenWebUI container
- Downloads models (30-60 minutes)

**Total Duration**: 45-90 minutes across both runs (mostly model downloads)

### 8. Verify Deployment

```bash
ansible-playbook playbooks/verify.yml
```

Expected: All services healthy ✅

## Access Your LLM Server

### From Mac mini directly:
```bash
open http://127.0.0.1:3000
```

### From your control machine (SSH tunnel):
```bash
ssh -L 3000:127.0.0.1:3000 user@mac-mini-ip

# Then open in browser:
open http://localhost:3000
```

## What You Get

- ✅ Ollama runtime (8 models)
- ✅ OpenWebUI web interface
- ✅ Docker Desktop
- ✅ Homebrew package management

### Available Models

1. llama3.1:8b - General purpose
2. deepseek-r1:8b - Reasoning
3. qwen3:8b - Multilingual
4. qwen2.5-coder:7b - Code generation
5. qwen3-vl:8b - Vision + language
6. bge-m3:latest - Embeddings
7. nomic-embed-text:latest - Text embeddings
8. x/z-image-turbo:fp8 - Image generation

## Common Operations

### Check Status
```bash
ansible-playbook playbooks/verify.yml
```

### Update Models
```bash
ansible-playbook playbooks/site.yml -e ollama_models_refresh=true --tags models
```

### Upgrade Components
```bash
# 1. Edit inventory/group_vars/all.yml (update version pins)
# 2. Run with upgrades enabled
ansible-playbook playbooks/site.yml -e enable_upgrades=true
```

### Restart Services
```bash
# SSH to Mac mini
ssh user@mac-mini

# Restart Ollama
brew services restart ollama

# Restart OpenWebUI
cd /path/to/compose/openwebui
docker compose restart
```

## Troubleshooting

### Missing sudo password

**Error**: `fatal: [macmini_primary]: FAILED! => {"msg": "Missing sudo password"}`

**Fix**: Configure passwordless sudo (see Step 3) or run with:
```bash
ansible-playbook playbooks/site.yml --ask-become-pass
```

### Ollama not responding
```bash
ssh user@mac-mini "brew services restart ollama"
curl http://127.0.0.1:11434/api/tags  # Should return JSON
```

### Docker not running
```bash
# On Mac mini, manually open Docker Desktop
open -a Docker

# Wait for Docker to start
docker ps
```

### OpenWebUI not accessible
```bash
ssh user@mac-mini "docker logs openwebui --tail 50"
```

### Models taking too long
- Normal: Large models (8B parameters) can take 30-60 minutes each
- Monitor progress: `ssh user@mac-mini "ollama list"`

## Next Steps

- **Full documentation**: See `README.md`
- **Architecture**: See `AGENTS.md`
- **Deployment guide**: See `docs/DEPLOYMENT.md`
- **Upgrades**: See `docs/UPGRADES.md`
- **Testing**: See `TESTING.md`

## Get Help

- Review logs: `docker logs openwebui`
- Check Ollama: `ollama list`
- Re-run verify: `ansible-playbook playbooks/verify.yml`
- Open GitHub issue with error details

---

**Ready to provision?** Run `ansible-playbook playbooks/site.yml` 🚀
