---
layout: default
title: Home
---

# Haymaker M365 Workloads

Microsoft 365 Knowledge Worker workloads for the [Agent Haymaker](https://github.com/rysweet/agent-haymaker) platform.

This workload simulates realistic M365 knowledge workers performing everyday activities -- email, Teams messaging, calendar events, and document collaboration -- organized into departments with distinct activity patterns that mirror real organizational behavior.

## Documentation

- [AI Email Generation](ai-email-generation.md) -- LLM-powered email content, department prompts, custom directives, fallback behavior
- [Configuration Reference](configuration.md) -- All workload options, YAML config examples, environment variables
- [Architecture](architecture.md) -- Module structure, platform integration, deployment lifecycle

## Quick Start

### 1. Install

```bash
# Via haymaker CLI
haymaker workload install https://github.com/rysweet/haymaker-m365-workloads

# Or via pip
pip install haymaker-m365-workloads

# With AI email generation support
pip install "haymaker-m365-workloads[ai]"
```

### 2. Set credentials

```bash
export KW_TENANT_ID="your-tenant-id"
export KW_APP_ID="your-app-client-id"
export KW_CLIENT_SECRET="your-client-secret"  # pragma: allowlist secret
```

### 3. Deploy

```bash
haymaker deploy m365-knowledge-worker \
  --config workers=25 \
  --config department=operations
```

### 4. Monitor and manage

```bash
haymaker status <deployment-id>
haymaker logs <deployment-id> --follow
haymaker stop <deployment-id>
haymaker cleanup <deployment-id>
```

## Department Activity Patterns

Each department has distinct activity rates that reflect real-world organizational behavior:

| Department | Email/hr | Teams/hr | Docs/day | Meetings/day |
|------------|----------|----------|----------|--------------|
| Operations | 6 | 8 | 4 | 4 |
| Engineering | 4 | 15 | 6 | 3 |
| Sales | 12 | 10 | 3 | 8 |
| HR | 10 | 8 | 5 | 5 |
| Finance | 6 | 5 | 8 | 4 |
| Executive | 8 | 5 | 2 | 10 |

Activity rates include a configurable variance (default 30%) to produce natural-looking patterns rather than uniform traffic.

## Security Model

- **Internal-only email** -- Exchange transport rules block external recipients
- **Ephemeral credentials** -- Worker passwords are generated and not stored
- **Isolated users** -- Workers are created in Entra with minimal permissions
- **Automatic cleanup** -- `haymaker cleanup` removes all Entra resources

## Prerequisites

An Azure AD application registration with the following Microsoft Graph API permissions (Application type):

| Permission | Description |
|------------|-------------|
| `User.ReadWrite.All` | Create and manage worker users |
| `Group.ReadWrite.All` | Create and manage security groups |
| `Mail.Send` | Send email as workers |
| `Mail.ReadWrite` | Read and organize email |
| `ChannelMessage.Send` | Post Teams messages |
| `Files.ReadWrite.All` | Document operations |
| `Calendars.ReadWrite` | Calendar operations |

## Links

- [Agent Haymaker Platform](https://github.com/rysweet/agent-haymaker)
- [Source Repository](https://github.com/rysweet/haymaker-m365-workloads)
