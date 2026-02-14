# Common Role

## Purpose

Provides shared setup, assertions, and preconditions for all other roles.

## Responsibilities

- Ensure the data directory structure exists (`/opt/local-llm` and subdirectories)
- Verify required variables are defined
- Create necessary directories with appropriate permissions
- Provide foundation for other roles

## Variables

None specific to this role. Uses variables from `group_vars/all.yml`:
- `local_llm_data_dir`
- `ollama_models_dir`
- `openwebui_data_dir`

## Dependencies

None.

## Tags

- `always` - Runs for all playbook executions
- `preflight` - Included in preflight checks

## Idempotency

Fully idempotent. Safe to run multiple times.
