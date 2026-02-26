---
layout: default
title: Architecture
---

# Architecture

Technical architecture of the M365 Knowledge Worker workload.

## Module Structure

```
haymaker_m365_workloads/
├── __init__.py                  Package entry; exports M365KnowledgeWorkerWorkload
├── workload.py                  Main workload class (deploy, stop, cleanup, status)
├── identity/
│   ├── __init__.py
│   └── user_manager.py          EntraUserManager -- creates/deletes Entra ID users
├── operations/
│   ├── __init__.py
│   └── orchestrator.py          ActivityOrchestrator -- runs the activity loop
├── content/
│   ├── __init__.py
│   ├── email_generator.py       EmailGenerator -- LLM + template fallback
│   └── prompts.py               Department-aware prompt templates
└── models/
    ├── __init__.py
    └── worker.py                WorkerIdentity, WorkerConfig, Department, ActivityPattern
```

### workload.py

`M365KnowledgeWorkerWorkload` extends `WorkloadBase` from the agent-haymaker platform. It is the top-level entry point registered via the `workload.yaml` manifest:

```yaml
package:
  entrypoint: haymaker_m365_workloads:M365KnowledgeWorkerWorkload
```

Responsibilities:
- Parse and validate deployment configuration
- Create the `EntraUserManager` and `EmailGenerator` instances
- Provision worker identities in Entra ID
- Start the `ActivityOrchestrator` for continuous activity generation
- Expose `deploy`, `stop`, `cleanup`, `get_status`, and `get_logs` to the platform

### identity/user_manager.py

`EntraUserManager` handles all Entra ID (Azure AD) operations through the Microsoft Graph API:

- `create_worker(config)` -- creates an Entra user with a generated UPN and secure random password
- `delete_worker(worker_id)` -- removes a single Entra user
- `delete_all_workers()` -- removes all workers created by this manager instance
- `get_workers()` -- returns all tracked worker identities

Worker credentials are ephemeral: passwords are generated at creation time and never stored.

### operations/orchestrator.py

`ActivityOrchestrator` runs the continuous activity generation loop:

- Iterates over all workers each cycle (one cycle per minute)
- Checks work hours for each worker (default 08:00--17:00 UTC)
- Probabilistically triggers activities based on the worker's department pattern
- Calls `EmailGenerator.generate()` for email content when available
- Logs each activity and invokes the `on_activity` callback for telemetry
- Supports `start()`, `stop()`, and `get_logs()` with optional follow mode

### content/email_generator.py

`EmailGenerator` produces realistic email content:

- If an LLM client is available: builds a department-aware prompt, calls the LLM, and parses the response into subject and body
- If no LLM is available (missing dependency, API error, rate limit): falls back to rotating department-specific templates
- Accepts an optional `email_directive` for custom topic steering
- The fallback path ensures telemetry generation continues regardless of LLM availability

### models/worker.py

Data models used across the workload:

- `Department` -- enum of valid departments (operations, engineering, sales, hr, finance, executive)
- `ActivityPattern` -- per-department activity rates (email/hr, Teams/hr, docs/day, meetings/day) plus work hours and variance
- `WorkerConfig` -- input for creating a new worker (department, worker number, deployment ID)
- `WorkerIdentity` -- a created worker with Entra object ID, UPN, department, and activity pattern

`DEPARTMENT_PATTERNS` is a dictionary mapping each `Department` to its `ActivityPattern`.

## Platform Integration

The workload integrates with agent-haymaker through the `WorkloadBase` interface:

```
agent-haymaker platform
  └── WorkloadBase (abstract)
        └── M365KnowledgeWorkerWorkload
              ├── deploy(config) -> deployment_id
              ├── get_status(deployment_id) -> DeploymentState
              ├── stop(deployment_id) -> bool
              ├── cleanup(deployment_id) -> CleanupReport
              ├── get_logs(deployment_id) -> AsyncIterator[str]
              ├── validate_config(config) -> list[str]
              └── list_deployments() -> list[DeploymentState]
```

The platform handles:
- CLI commands (`haymaker deploy`, `haymaker status`, etc.)
- Credential management (environment variables or Key Vault)
- State persistence (`save_state` / `load_state`)
- Workload registration from `workload.yaml`

## Deployment Lifecycle

A deployment moves through the following phases:

```
PENDING
  │
  ▼
creating_workers    Create Entra ID users via Graph API
  │
  ▼
executing           Activity loop running (email, Teams, calendar, documents)
  │
  ├──▶ stopped      Manual stop via `haymaker stop`
  │
  ▼
cleanup             Delete Entra users and resources via `haymaker cleanup`
  │
  ├──▶ completed    All resources removed
  │
  └──▶ failed       Cleanup error (resources may remain)
```

State transitions are persisted through the platform's `save_state` mechanism, allowing deployments to be tracked across process restarts.

## Activity Generation Loop

The orchestrator runs a continuous loop with one-minute cycles:

```
while running:
    if duration_hours exceeded:
        break

    for each worker:
        if outside work hours (08:00-17:00 UTC):
            skip

        if random() < email_per_hour / 60:
            send email (via EmailGenerator if available)

        if random() < teams_per_hour / 60:
            send Teams message

        if random() < docs_per_day / 480:
            create document

    sleep 60 seconds
```

Each activity:
1. Is probabilistically triggered based on the department's per-hour rate
2. Generates content (AI or template for email; placeholder for Teams/documents)
3. Logs the activity with timestamp and worker identity
4. Fires the `on_activity` callback for telemetry aggregation

The per-minute probability is `rate_per_hour / 60`, which produces the expected hourly rate over time while maintaining natural variance between cycles.
