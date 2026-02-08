# Upgrade Procedures

This document describes how to safely upgrade components of the local LLM server.

## General Upgrade Policy

All upgrades follow these principles (see AGENTS.md section 14):

1. **Intentional:** Upgrades require explicit variable changes and are never automatic.
2. **Tested:** Always test in `--check` mode first.
3. **Rollback-aware:** Know how to revert if something breaks.
4. **Documented:** Record what changed and why.

## Safety Checklist

Before any upgrade:

- [ ] Backup important data or snapshots
- [ ] Read release notes for breaking changes
- [ ] Run `ansible-playbook playbooks/verify.yml` to establish baseline
- [ ] Run `ansible-playbook playbooks/site.yml --check -e enable_upgrades=true` to preview changes
- [ ] Have a rollback plan (previous version known and tested)

## Component-Specific Procedures

### Ollama Upgrade

**Current version:** See `group_vars/all.yml` → `ollama_version`

**Procedure:**

1. Check [Ollama releases](https://github.com/ollama/ollama/releases) for new versions

2. Update `group_vars/all.yml`:
   ```yaml
   ollama_version: "0.4.0"  # new version
   ```

3. Dry-run:
   ```bash
   ansible-playbook playbooks/site.yml --check -e enable_upgrades=true --tags ollama
   ```

4. If dry-run looks safe, apply:
   ```bash
   ansible-playbook playbooks/site.yml -e enable_upgrades=true --tags ollama
   ```

5. Verify:
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

6. Test model operations (pull, list, run):
   ```bash
   ssh <user>@<host> "ollama list"
   ```

**Rollback:**
- Revert `group_vars/all.yml` to previous version
- Re-run provisioning playbook

### Docker Desktop Upgrade

**Current version:** See `group_vars/all.yml` → `docker_desktop_version`

**Procedure:**

1. Check [Docker Desktop releases](https://docs.docker.com/desktop/release-notes/) for macOS

2. Update `group_vars/all.yml`:
   ```yaml
   docker_desktop_version: "27.1.0"  # new version
   ```

3. Dry-run:
   ```bash
   ansible-playbook playbooks/site.yml --check -e enable_upgrades=true --tags docker_desktop
   ```

4. Apply (may require manual restart on first run due to macOS security):
   ```bash
   ansible-playbook playbooks/site.yml -e enable_upgrades=true --tags docker_desktop
   ```

5. If prompted, manually restart Docker Desktop (GUI or `open /Applications/Docker.app`)

6. Verify:
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

**Rollback:**
- Download previous Docker Desktop version from Docker Hub
- Manually install and restart

### Homebrew Packages Upgrade

**Current versions:** Defined in `homebrew` role (when created)

**Procedure:**

1. Review what packages are managed (see role definition)

2. Update version pins in role or group_vars

3. Dry-run:
   ```bash
   ansible-playbook playbooks/site.yml --check -e enable_upgrades=true --tags homebrew
   ```

4. Apply:
   ```bash
   ansible-playbook playbooks/site.yml -e enable_upgrades=true --tags homebrew
   ```

5. Verify:
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

**Rollback:**
- Reinstall previous versions:
  ```bash
  brew install <package>@<version>
  ```

### OpenWebUI Container Image Upgrade

**Current version:** See `group_vars/all.yml` → `openwebui_image_tag`

**Procedure:**

1. Check [OpenWebUI releases](https://github.com/open-webui/open-webui/releases) for new tags

2. Update `group_vars/all.yml`:
   ```yaml
   openwebui_image_tag: "v1.2.0"  # or container digest
   ```

3. Dry-run:
   ```bash
   ansible-playbook playbooks/site.yml --check -e enable_upgrades=true --tags openwebui
   ```

4. Apply (pulls new image and restarts container):
   ```bash
   ansible-playbook playbooks/site.yml -e enable_upgrades=true --tags openwebui
   ```

5. Monitor Docker logs:
   ```bash
   ssh <user>@<host> "docker logs -f openwebui"
   ```

6. Verify:
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

**Rollback:**
- Revert to previous tag in `group_vars/all.yml`
- Re-run provisioning playbook

### Ollama Models Refresh

If you want to **repull all models** (full refresh):

```bash
ansible-playbook playbooks/site.yml -e ollama_models_refresh=true --tags models
```

**Warning:** This will take time (models are large). Useful after Ollama major version upgrades.

### Ollama Models Prune

If you want to **remove models not declared** in `ollama_models`:

```bash
ansible-playbook playbooks/site.yml -e ollama_models_prune=true --tags models
```

**Warning:** This is destructive. Only use after verifying what will be removed:
```bash
ssh <user>@<host> "ollama list"
```

## Monitoring After Upgrades

1. **Service health:** Run `playbooks/verify.yml`
2. **Logs:** Check application logs:
   ```bash
   ssh <user>@<host> "docker logs openwebui"
   ssh <user>@<host> "docker logs ollama" (if containerized)
   ```
3. **Model functionality:** Test model inference:
   ```bash
   ssh <user>@<host> "ollama run llama3.1:8b 'Hello'"
   ```

## If Something Breaks

1. **Stop affected services** (if needed):
   ```bash
   ssh <user>@<host> \
     "docker stop openwebui && \
      sudo launchctl stop ollama"  # or equivalent
   ```

2. **Revert configuration:**
   - Edit `group_vars/all.yml` to previous versions

3. **Reinstall/revert:**
   ```bash
   ansible-playbook playbooks/site.yml -e enable_upgrades=true
   ```

4. **Test connectivity:**
   ```bash
   ansible-playbook playbooks/verify.yml
   ```

5. **Document the incident** in issue/PR for future reference

## Breaking Changes Log

Track known issues and mitigation:

| Version | Component | Issue | Mitigation |
|---------|-----------|-------|------------|
| TBD     | TBD       | TBD   | TBD        |

---

For principles and governance, see [AGENTS.md](../AGENTS.md).
For operational overview, see [docs/SETUP.md](../docs/SETUP.md).
