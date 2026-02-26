"""M365 Knowledge Worker Workload implementation.

Simulates realistic Microsoft 365 knowledge workers performing
everyday activities like email, Teams, calendar, and documents.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Any

from agent_haymaker import (
    WorkloadBase,
    DeploymentState,
    DeploymentConfig,
)
from agent_haymaker.workloads.models import CleanupReport, DeploymentStatus

from .models.worker import WorkerConfig, WorkerIdentity, Department
from .identity.user_manager import EntraUserManager
from .operations.orchestrator import ActivityOrchestrator
from .content.email_generator import EmailGenerator

logger = logging.getLogger(__name__)


class M365KnowledgeWorkerWorkload(WorkloadBase):
    """Workload for simulating M365 knowledge workers.

    This workload:
    1. Creates Entra ID users for workers
    2. Organizes workers into departments/teams
    3. Runs continuous M365 activity generation
    4. Collects telemetry on activities performed
    5. Cleans up Entra users and resources
    """

    name = "m365-knowledge-worker"

    def __init__(self, platform: Any = None) -> None:
        super().__init__(platform)
        self._deployments: dict[str, DeploymentState] = {}
        self._orchestrators: dict[str, ActivityOrchestrator] = {}
        self._user_managers: dict[str, EntraUserManager] = {}

    async def deploy(self, config: DeploymentConfig) -> str:
        """Deploy M365 knowledge workers.

        Args:
            config: Must include workload_config with:
                - workers: Number of workers to create (default: 25)
                - department: Department type (operations, engineering, sales, etc.)
                - duration_hours: How long to run (None = indefinite)
                - enable_ai_generation: Use AI for email content (default: False)

        Returns:
            deployment_id for tracking
        """
        # Extract configuration
        num_workers = config.workload_config.get("workers", 25)
        department = config.workload_config.get("department", "operations")
        duration_hours = config.duration_hours
        enable_ai = config.workload_config.get("enable_ai_generation", False)
        email_directive = config.workload_config.get("email_directive")

        # Generate deployment ID
        deployment_id = f"m365-{uuid.uuid4().hex[:8]}"

        # Create deployment state
        state = DeploymentState(
            deployment_id=deployment_id,
            workload_name=self.name,
            status=DeploymentStatus.PENDING,
            phase="initializing",
            started_at=datetime.utcnow(),
            config={
                "workers": num_workers,
                "department": department,
                "duration_hours": duration_hours,
                "enable_ai_generation": enable_ai,
                **config.workload_config,
            },
            metadata={
                "workers_created": 0,
                "activities_performed": 0,
            },
        )
        self._deployments[deployment_id] = state

        # Initialize components
        user_manager = EntraUserManager(
            deployment_id=deployment_id,
            get_credential=self.get_credential,
        )
        self._user_managers[deployment_id] = user_manager

        # Create email generator (with optional LLM client)
        email_generator = self._create_email_generator(enable_ai, email_directive)

        # Create workers
        state.phase = "creating_workers"
        await self.save_state(state)

        workers = await self._create_workers(
            user_manager=user_manager,
            num_workers=num_workers,
            department=department,
            deployment_id=deployment_id,
        )

        state.metadata["workers_created"] = len(workers)

        # Start activity orchestrator
        orchestrator = ActivityOrchestrator(
            deployment_id=deployment_id,
            workers=workers,
            enable_ai=enable_ai,
            duration_hours=duration_hours,
            on_activity=lambda activity: self._on_activity(deployment_id, activity),
            email_generator=email_generator,
        )
        self._orchestrators[deployment_id] = orchestrator

        # Start execution
        state.status = DeploymentStatus.RUNNING
        state.phase = "executing"
        await self.save_state(state)

        await orchestrator.start()

        return deployment_id

    async def get_status(self, deployment_id: str) -> DeploymentState:
        """Get current deployment state."""
        state = self._deployments.get(deployment_id)
        if not state:
            state = await self.load_state(deployment_id)
            if state:
                self._deployments[deployment_id] = state

        if not state:
            from agent_haymaker.workloads.base import DeploymentNotFoundError

            raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")

        # Update activity count from orchestrator
        orchestrator = self._orchestrators.get(deployment_id)
        if orchestrator:
            state.metadata["activities_performed"] = orchestrator.activity_count

        return state

    async def stop(self, deployment_id: str) -> bool:
        """Stop a running deployment."""
        state = await self.get_status(deployment_id)
        orchestrator = self._orchestrators.get(deployment_id)

        if orchestrator:
            await orchestrator.stop()

        state.status = DeploymentStatus.STOPPED
        state.phase = "stopped"
        state.stopped_at = datetime.utcnow()
        await self.save_state(state)

        return True

    async def cleanup(self, deployment_id: str) -> CleanupReport:
        """Clean up all resources for a deployment.

        Deletes:
        - Entra ID users
        - Security groups
        - Exchange transport rules
        - Any provisioned endpoints
        """
        state = await self.get_status(deployment_id)
        orchestrator = self._orchestrators.get(deployment_id)
        user_manager = self._user_managers.get(deployment_id)

        report = CleanupReport(deployment_id=deployment_id)

        try:
            # Stop orchestrator if running
            if orchestrator and state.status == DeploymentStatus.RUNNING:
                await orchestrator.stop()

            state.status = DeploymentStatus.CLEANING_UP
            state.phase = "cleanup"
            await self.save_state(state)

            # Delete Entra users
            if user_manager:
                deleted = await user_manager.delete_all_workers()
                report.resources_deleted += deleted
                report.details.append(f"Deleted {deleted} Entra users")

            # Mark completed
            state.status = DeploymentStatus.COMPLETED
            state.phase = "cleaned_up"
            state.completed_at = datetime.utcnow()
            await self.save_state(state)

        except Exception as e:
            report.errors.append(str(e))
            state.status = DeploymentStatus.FAILED
            state.error = str(e)
            await self.save_state(state)

        return report

    async def get_logs(
        self, deployment_id: str, follow: bool = False, lines: int = 100
    ) -> AsyncIterator[str]:
        """Stream logs for a deployment."""
        await self.get_status(deployment_id)  # Validates deployment exists
        orchestrator = self._orchestrators.get(deployment_id)

        if orchestrator:
            async for line in orchestrator.get_logs(follow=follow, lines=lines):
                yield line
        else:
            # Try loading from log file
            log_file = Path(f".haymaker/logs/{deployment_id}/activity.log")
            if log_file.exists():
                with open(log_file) as f:
                    for line in f.readlines()[-lines:]:
                        yield line

    async def validate_config(self, config: DeploymentConfig) -> list[str]:
        """Validate deployment configuration."""
        errors = await super().validate_config(config)

        workers = config.workload_config.get("workers", 25)
        if not isinstance(workers, int) or workers < 1:
            errors.append("'workers' must be a positive integer")
        if workers > 300:
            errors.append("'workers' cannot exceed 300")

        department = config.workload_config.get("department", "operations")
        valid_departments = ["operations", "engineering", "sales", "hr", "finance", "executive"]
        if department not in valid_departments:
            errors.append(f"'department' must be one of: {', '.join(valid_departments)}")

        enable_ai = config.workload_config.get("enable_ai_generation", False)
        if not isinstance(enable_ai, bool):
            errors.append("'enable_ai_generation' must be a boolean")

        email_directive = config.workload_config.get("email_directive")
        if email_directive is not None and not isinstance(email_directive, str):
            errors.append("'email_directive' must be a string")

        return errors

    async def list_deployments(self) -> list[DeploymentState]:
        """List all M365 Knowledge Worker deployments."""
        states = list(self._deployments.values())

        if self._platform:
            persisted = await self._platform.list_deployments(self.name)
            existing_ids = {s.deployment_id for s in states}
            for p in persisted:
                if p.deployment_id not in existing_ids:
                    states.append(p)

        return states

    def _create_email_generator(self, enable_ai: bool, directive: str | None) -> EmailGenerator:
        """Create an EmailGenerator, optionally with an LLM client.

        Args:
            enable_ai: Whether to attempt LLM-backed generation
            directive: Optional custom directive for email content

        Returns:
            EmailGenerator instance (always created; LLM client attached only
            when enable_ai is True and dependencies are available)
        """
        llm_client = None

        if enable_ai:
            try:
                from agent_haymaker.llm import LLMConfig, create_llm_client

                llm_config = LLMConfig()
                llm_client = create_llm_client(llm_config)
                logger.info("AI email generation enabled with LLM client")
            except ImportError:
                logger.warning(
                    "agent_haymaker[llm] not installed; "
                    "AI email generation will use template fallback"
                )
            except Exception as e:
                logger.warning(f"Failed to create LLM client: {e}; using template fallback")

        return EmailGenerator(llm_client=llm_client, directive=directive)

    async def _create_workers(
        self,
        user_manager: EntraUserManager,
        num_workers: int,
        department: str,
        deployment_id: str,
    ) -> list[WorkerIdentity]:
        """Create worker identities in Entra ID."""
        workers = []

        for i in range(num_workers):
            worker_config = WorkerConfig(
                department=Department(department),
                worker_number=i + 1,
                deployment_id=deployment_id,
            )

            try:
                worker = await user_manager.create_worker(worker_config)
                workers.append(worker)
            except Exception as e:
                self.log(f"Failed to create worker {i + 1}: {e}", level="ERROR")

        return workers

    def _on_activity(self, deployment_id: str, activity: dict) -> None:
        """Callback when an activity is performed."""
        state = self._deployments.get(deployment_id)
        if state:
            count = state.metadata.get("activities_performed", 0)
            state.metadata["activities_performed"] = count + 1
