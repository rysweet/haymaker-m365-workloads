---
layout: default
title: AI Email Generation
---

# AI Email Generation

The M365 Knowledge Worker workload supports AI-powered email content generation using the LLM abstraction layer from agent-haymaker.

## Overview

When `enable_ai_generation` is set to `true`, the workload uses an LLM provider to generate realistic, department-appropriate email content. When the LLM is unavailable, it falls back to template-based content.

## Enabling AI Email Generation

### Via CLI

```bash
haymaker deploy m365-knowledge-worker \
  --config workers=25 \
  --config department=sales \
  --config enable_ai_generation=true \
  --config email_directive="Write about Q4 targets"
```

### Via Config File

```yaml
# ai-email-deployment.yaml
workload_name: m365-knowledge-worker
workers: 10
department: sales
duration_hours: 4
enable_ai_generation: true
email_directive: "Write emails about Q4 sales targets and client relationships"
```

## Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_ai_generation` | bool | `false` | Enable LLM-powered content |
| `email_directive` | string | `null` | Custom directive for email topics |

## How It Works

1. **Deploy phase**: Workload checks `enable_ai_generation` and creates LLM client
2. **Activity phase**: Each email activity uses `EmailGenerator`:
   - If LLM available: generates content via LLM with department-aware prompts
   - If LLM fails: falls back to template-based content
   - Logs generated subject line for observability

## Department-Aware Prompts

Email content varies by department:

| Department | Typical Topics |
|------------|---------------|
| Engineering | Code reviews, sprint updates, technical decisions |
| Sales | Client meetings, deal progress, quarterly targets |
| HR | Policy updates, onboarding, team events |
| Finance | Budget reviews, expense reports, financial planning |
| Operations | Process improvement, vendor coordination, logistics |
| Executive | Strategic initiatives, board preparation, organizational updates |

## Custom Directives

The `email_directive` parameter lets you customize the email generation:

```yaml
# Limerick-style emails
email_directive: "Write all emails as limericks"

# Specific business context
email_directive: "Emails should reference the upcoming product launch"
```

## LLM Provider Setup

AI email generation requires an LLM provider. Set environment variables before deploying:

```bash
# Anthropic
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or Azure OpenAI
export LLM_PROVIDER=azure_openai
export AZURE_OPENAI_ENDPOINT=https://myresource.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT=gpt-4
```

Install AI dependencies:
```bash
pip install haymaker-m365-workloads[ai]
```

## Fallback Behavior

If the LLM is unavailable (not configured, API error, rate limited), the system falls back to rotating department-specific email templates. This ensures telemetry generation continues even without AI.

## Architecture

```
haymaker_m365_workloads/
├── content/
│   ├── email_generator.py   EmailGenerator (LLM + fallback)
│   └── prompts.py           Department-aware prompt templates
├── workload.py              LLM client creation on deploy
└── operations/
    └── orchestrator.py      Uses EmailGenerator for email activities
```
