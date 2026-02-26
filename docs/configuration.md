---
layout: default
title: Configuration Reference
---

# Configuration Reference

All configuration options for the M365 Knowledge Worker workload.

## Workload Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `workers` | integer | `25` | Number of knowledge workers to simulate (1--300) |
| `department` | string | `operations` | Department type. One of: `operations`, `engineering`, `sales`, `hr`, `finance`, `executive` |
| `duration_hours` | integer | `null` | Duration in hours. `null` runs indefinitely until stopped |
| `enable_ai_generation` | boolean | `false` | Enable LLM-powered email content generation |
| `email_directive` | string | `null` | Custom directive for AI email generation topics |

## Setting Options via CLI

Pass options as `--config key=value` flags:

```bash
haymaker deploy m365-knowledge-worker \
  --config workers=50 \
  --config department=sales \
  --config duration_hours=8 \
  --config enable_ai_generation=true \
  --config email_directive="Write about Q4 targets"
```

## YAML Configuration Files

You can also deploy from a YAML config file. Store these in the `examples/` directory or pass them directly.

### Basic Deployment

```yaml
# examples/basic-deployment.yaml
workload_name: m365-knowledge-worker
workers: 25
department: engineering
duration_hours: 8
```

Deploy with:

```bash
haymaker deploy -f examples/basic-deployment.yaml
```

### AI Email Deployment

```yaml
# examples/ai-email-deployment.yaml
workload_name: m365-knowledge-worker
workers: 10
department: sales
duration_hours: 4
enable_ai_generation: true
email_directive: "Write emails about Q4 sales targets and client relationships"
```

Deploy with:

```bash
haymaker deploy -f examples/ai-email-deployment.yaml
```

## Environment Variables

### Required -- M365 Credentials

These credentials authenticate against the Azure AD application registration that has Microsoft Graph API permissions.

| Variable | Description |
|----------|-------------|
| `KW_TENANT_ID` | Azure AD tenant ID |
| `KW_APP_ID` | Application (client) ID with Graph permissions |
| `KW_CLIENT_SECRET` | Client secret for the application |

```bash
export KW_TENANT_ID="your-tenant-id"
export KW_APP_ID="your-app-client-id"
export KW_CLIENT_SECRET="your-client-secret"  # pragma: allowlist secret
```

These can also be stored in Azure Key Vault and retrieved by the platform at runtime.

### Optional -- LLM Provider

Required only when `enable_ai_generation` is `true`. The workload uses the `agent-haymaker[llm]` abstraction layer, which supports multiple providers.

#### Anthropic

```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY="sk-ant-..."  # pragma: allowlist secret
```

#### Azure OpenAI

```bash
export LLM_PROVIDER=azure_openai
export AZURE_OPENAI_ENDPOINT="https://myresource.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4"
```

Install AI dependencies:

```bash
pip install "haymaker-m365-workloads[ai]"
```

If the LLM provider is not configured or the API key is missing, the workload falls back to rotating department-specific email templates automatically. No error is raised -- telemetry generation continues normally.

## Department Activity Patterns

Each department defines its own activity rates. These are built into the workload and selected by the `department` configuration option.

| Department | Email/hr | Teams/hr | Docs/day | Meetings/day |
|------------|----------|----------|----------|--------------|
| `operations` | 6 | 8 | 4 | 4 |
| `engineering` | 4 | 15 | 6 | 3 |
| `sales` | 12 | 10 | 3 | 8 |
| `hr` | 10 | 8 | 5 | 5 |
| `finance` | 6 | 5 | 8 | 4 |
| `executive` | 8 | 5 | 2 | 10 |

Additional pattern parameters (configured per department, not user-facing):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `activity_variance_percent` | `30` | Random variance applied to activity rates |
| `work_start_hour` | `8` | Start of work hours (UTC) |
| `work_end_hour` | `17` | End of work hours (UTC) |

## Workload Manifest

The workload is described by `workload.yaml` at the repository root. This manifest declares the workload name, package entrypoint, required permissions, credentials, and configuration schema. The `haymaker workload install` command reads this file to register the workload with the platform.

## Validation

The workload validates configuration at deploy time:

- `workers` must be a positive integer, maximum 300
- `department` must be one of the six valid department names
- `enable_ai_generation` must be a boolean
- `email_directive` must be a string (if provided)

Invalid configuration returns a list of error messages before any resources are created.
