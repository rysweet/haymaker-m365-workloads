# Haymaker M365 Workloads

Microsoft 365 Knowledge Worker workloads for Agent Haymaker platform.

## Overview

This package simulates realistic M365 knowledge workers performing everyday activities:

- **Email** - Send, receive, organize, and reply to emails
- **Microsoft Teams** - Channel posts, direct messages, reactions
- **Calendar** - Events, meetings, scheduling
- **Documents** - OneDrive and SharePoint operations

Workers are organized into departments with distinct activity patterns that mirror real organizational behavior.

## Installation

```bash
# Install via haymaker CLI
haymaker workload install https://github.com/rysweet/haymaker-m365-workloads

# Or via pip
pip install haymaker-m365-workloads

# With AI email generation support
pip install "haymaker-m365-workloads[ai]"
```

## Prerequisites

### M365 App Registration

Create an Azure AD application with the following Graph API permissions:

| Permission | Type | Description |
|------------|------|-------------|
| `User.ReadWrite.All` | Application | Create/manage worker users |
| `Group.ReadWrite.All` | Application | Create/manage security groups |
| `Mail.Send` | Application | Send email as workers |
| `Mail.ReadWrite` | Application | Read/organize email |
| `ChannelMessage.Send` | Application | Post Teams messages |
| `Files.ReadWrite.All` | Application | Document operations |
| `Calendars.ReadWrite` | Application | Calendar operations |

### Required Credentials

Set these in your environment or Key Vault:

```bash
export KW_TENANT_ID="your-tenant-id"
export KW_APP_ID="your-app-client-id"
export KW_CLIENT_SECRET="your-client-secret"

# Optional: For AI-powered email generation
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Usage

```bash
# Deploy 25 workers in operations department
haymaker deploy m365-knowledge-worker --config workers=25 --config department=operations

# With AI email generation
haymaker deploy m365-knowledge-worker \
  --config workers=50 \
  --config department=sales \
  --config enable_ai_generation=true

# Run for specific duration
haymaker deploy m365-knowledge-worker \
  --config workers=25 \
  --duration 4

# Monitor
haymaker status <deployment-id>
haymaker logs <deployment-id> --follow

# Stop
haymaker stop <deployment-id>

# Cleanup (deletes Entra users)
haymaker cleanup <deployment-id>
```

## Departments

Each department has distinct activity patterns:

| Department | Email/hr | Teams/hr | Docs/day | Meetings/day |
|------------|----------|----------|----------|--------------|
| Operations | 6 | 8 | 4 | 4 |
| Engineering | 4 | 15 | 6 | 3 |
| Sales | 12 | 10 | 3 | 8 |
| HR | 10 | 8 | 5 | 5 |
| Finance | 6 | 5 | 8 | 4 |
| Executive | 8 | 5 | 2 | 10 |

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `workers` | int | 25 | Number of workers (1-300) |
| `department` | string | operations | Department type |
| `duration_hours` | int | null | Duration (null = indefinite) |
| `enable_ai_generation` | bool | false | Use AI for email content |
| `email_directive` | string | null | Custom directive for AI email generation |

## AI Email Generation

When `enable_ai_generation` is set to `true`, email content is generated using an LLM provider from `agent-haymaker[llm]`. This produces realistic, department-aware emails that vary across workers and cycles.

### How it works

1. The `EmailGenerator` checks for an available LLM client
2. If an LLM is available, it builds a department-specific prompt and generates unique email content
3. If no LLM is available (missing dependency or API key), it falls back to built-in templates
4. Fallback templates rotate through department-specific email scenarios

### Enabling AI generation

```bash
# Install with AI dependencies
pip install "haymaker-m365-workloads[ai]"

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Deploy with AI generation
haymaker deploy m365-knowledge-worker \
  --config workers=10 \
  --config department=sales \
  --config enable_ai_generation=true

# With a custom directive
haymaker deploy m365-knowledge-worker \
  --config workers=10 \
  --config department=engineering \
  --config enable_ai_generation=true \
  --config email_directive="Write emails about migrating to Kubernetes"
```

### Example deployment configs

See the `examples/` directory for sample YAML deployment configurations:

- `examples/basic-deployment.yaml` - Standard deployment without AI
- `examples/ai-email-deployment.yaml` - AI-enabled deployment with custom directive

## Security

- **Internal-only email**: Exchange transport rules block external recipients
- **Ephemeral credentials**: Worker passwords are generated and not stored
- **Isolated users**: Workers are created in Entra with minimal permissions
- **Automatic cleanup**: `haymaker cleanup` removes all Entra resources

## Telemetry

The workload generates telemetry including:

- Email send/receive counts
- Teams message counts
- Document operation counts
- Activity timestamps and patterns

Access telemetry via:
```bash
haymaker logs <deployment-id>
```

## Development

```bash
# Clone
git clone https://github.com/rysweet/haymaker-m365-workloads
cd haymaker-m365-workloads

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=haymaker_m365_workloads
```

## Architecture

```
M365KnowledgeWorkerWorkload
├── EntraUserManager
│   ├── create_worker()
│   ├── delete_worker()
│   └── delete_all_workers()
├── ActivityOrchestrator
│   ├── _send_email()
│   ├── _send_teams_message()
│   └── _create_document()
└── Models
    ├── WorkerIdentity
    ├── WorkerConfig
    └── ActivityPattern
```

## Documentation

- [AI Email Generation Guide](docs/ai-email-generation.md) - LLM-powered email content, department prompts, custom directives, fallback behavior

## License

MIT
