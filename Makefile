.PHONY: help lint lint-yaml lint-ansible check verify provision dry-run provision-upgrade clean
.PHONY: test validate test-all syntax-check

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Testing & Validation:"
	@echo "  test          - Run all validation checks (recommended before commit)"
	@echo "  test-all      - Run all tests including lint and validation"
	@echo "  lint          - Run all linters (ansible-lint + yamllint)"
	@echo "  lint-yaml     - Run yamllint only"
	@echo "  lint-ansible  - Run ansible-lint only"
	@echo "  syntax-check  - Run Ansible syntax check on all playbooks"
	@echo "  validate      - Run custom validation scripts"
	@echo ""
	@echo "Provisioning:"
	@echo "  check         - Run playbooks in --check mode (dry-run)"
	@echo "  verify        - Run connectivity verification playbook"
	@echo "  provision     - Run full provisioning (no upgrades)"
	@echo "  provision-upgrade - Run provisioning with upgrades enabled"
	@echo ""
	@echo "Maintenance:"
	@echo "  dry-run       - Alias for 'check'"
	@echo "  clean         - Remove ansible cache and local state"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "See TESTING.md for detailed testing documentation"

# Testing targets (what runs in CI)
test: lint-yaml syntax-check lint-ansible validate
	@echo ""
	@echo "✅ All validation checks passed!"
	@echo "Ready to commit."

test-all: lint validate
	@echo ""
	@echo "✅ All tests passed!"

# Linting targets
lint: lint-yaml lint-ansible

lint-yaml:
	@echo "Running yamllint..."
	yamllint .

lint-ansible:
	@echo "Running ansible-lint..."
	ansible-lint playbooks/ roles/

# Syntax check
syntax-check:
	@echo "Running Ansible syntax checks..."
	ansible-playbook --syntax-check playbooks/site.yml
	ansible-playbook --syntax-check playbooks/verify.yml
	ansible-playbook --syntax-check playbooks/preflight.yml

# Validation scripts
validate:
	@echo "Running validation scripts..."
	@echo ""
	@echo "→ Validating role structure..."
	python3 scripts/validate_structure.py
	@echo ""
	@echo "→ Validating model declarations..."
	python3 scripts/validate_models.py
	@echo ""
	@echo "→ Checking Darwin guards..."
	python3 scripts/check_darwin_guards.py
	@echo ""
	@echo "→ Checking idempotency patterns..."
	python3 scripts/validate_idempotency.py
	@echo ""
	@echo "✅ All validation scripts completed"

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
	rm -rf .ansible_facts_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	@echo "Clean complete"
