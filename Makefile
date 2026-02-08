.PHONY: help lint check verify provision dry-run upgrade clean

# Default target
help:
	@echo "Available targets:"
	@echo "  lint          - Run ansible-lint and yamllint"
	@echo "  check         - Run playbooks in --check mode (dry-run)"
	@echo "  verify        - Run connectivity verification playbook"
	@echo "  provision     - Run full provisioning (no upgrades)"
	@echo "  provision-upgrade - Run provisioning with upgrades enabled"
	@echo "  dry-run       - Alias for 'check'"
	@echo "  clean         - Remove ansible cache and local state"
	@echo "  help          - Show this help message"

# Linting targets
lint:
	@echo "Running ansible-lint..."
	ansible-lint playbooks/ roles/ || true
	@echo "Running yamllint..."
	yamllint . || true

# Check mode (dry-run) - safe, no changes
check:
	@echo "Running playbooks in --check mode (dry-run)..."
	ansible-playbook playbooks/site.yml --check

dry-run: check

# Connectivity verification
verify:
	@echo "Running connectivity verification..."
	ansible-playbook playbooks/verify.yml

# Provisioning (default: no upgrades)
provision:
	@echo "Running provisioning playbook (no upgrades)..."
	ansible-playbook playbooks/site.yml

# Provisioning with upgrades
provision-upgrade:
	@echo "Running provisioning with upgrades enabled..."
	ansible-playbook playbooks/site.yml -e enable_upgrades=true

# Clean local state
clean:
	@echo "Cleaning Ansible cache and local state..."
	rm -rf .ansible/
	rm -rf /tmp/ansible_facts_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	@echo "Clean complete"
