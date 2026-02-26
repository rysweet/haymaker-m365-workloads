"""Activity orchestrator for M365 knowledge workers.

Coordinates continuous M365 activity generation across all workers,
respecting activity patterns and work hours.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Callable, TYPE_CHECKING

from ..models.worker import WorkerIdentity

if TYPE_CHECKING:
    from ..content.email_generator import EmailGenerator


class ActivityOrchestrator:
    """Orchestrates M365 activity generation for workers.

    Manages:
    - Email sending/receiving
    - Teams messaging
    - Calendar events
    - Document operations

    Each worker follows their department's activity pattern.
    """

    def __init__(
        self,
        deployment_id: str,
        workers: list[WorkerIdentity],
        enable_ai: bool = False,
        duration_hours: int | None = None,
        on_activity: Callable[[dict], None] | None = None,
        email_generator: EmailGenerator | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            deployment_id: ID of the parent deployment
            workers: List of workers to orchestrate
            enable_ai: Whether to use AI for content generation
            duration_hours: Duration in hours (None = indefinite)
            on_activity: Callback when an activity is performed
            email_generator: Optional EmailGenerator for AI-powered content
        """
        self.deployment_id = deployment_id
        self.workers = workers
        self.enable_ai = enable_ai
        self.duration_hours = duration_hours
        self._on_activity = on_activity
        self._email_generator = email_generator

        self._running = False
        self._task: asyncio.Task | None = None
        self._logs: list[str] = []
        self._activity_count = 0
        self._log_file: Path | None = None

        self._setup_logging()

    @property
    def activity_count(self) -> int:
        """Total number of activities performed."""
        return self._activity_count

    def _setup_logging(self) -> None:
        """Set up log file."""
        log_dir = Path(f".haymaker/logs/{self.deployment_id}")
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = log_dir / "activity.log"

    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_line)

        if self._log_file:
            with open(self._log_file, "a") as f:
                f.write(log_line + "\n")

    async def start(self) -> None:
        """Start activity generation."""
        if self._running:
            return

        self._running = True
        self._log(f"Starting activity orchestration for {len(self.workers)} workers")
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop activity generation."""
        self._running = False
        self._log("Stopping activity orchestration")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def get_logs(self, follow: bool = False, lines: int = 100) -> AsyncIterator[str]:
        """Stream orchestrator logs."""
        for line in self._logs[-lines:]:
            yield line

        if follow:
            last_index = len(self._logs)
            while self._running:
                await asyncio.sleep(0.5)
                new_logs = self._logs[last_index:]
                for line in new_logs:
                    yield line
                last_index = len(self._logs)

    async def _run(self) -> None:
        """Main activity loop."""
        try:
            end_time = None
            if self.duration_hours:
                end_time = datetime.utcnow().timestamp() + (self.duration_hours * 3600)

            while self._running:
                # Check duration
                if end_time and datetime.utcnow().timestamp() >= end_time:
                    self._log("Duration limit reached")
                    break

                # Run activity cycle for all workers
                await self._run_activity_cycle()

                # Wait before next cycle
                await asyncio.sleep(60)  # 1 minute between cycles

            self._log("Activity orchestration completed")

        except asyncio.CancelledError:
            self._log("Activity orchestration cancelled")
            raise
        except Exception as e:
            self._log(f"Activity orchestration failed: {e}", "ERROR")
            raise

    async def _run_activity_cycle(self) -> None:
        """Run one activity cycle for all workers."""
        current_hour = datetime.utcnow().hour

        for worker in self.workers:
            # Check if within work hours
            pattern = worker.activity_pattern
            if not (pattern.work_start_hour <= current_hour < pattern.work_end_hour):
                continue

            # Perform activities based on pattern
            await self._perform_worker_activities(worker)

    async def _perform_worker_activities(self, worker: WorkerIdentity) -> None:
        """Perform activities for a single worker."""
        pattern = worker.activity_pattern

        # Email activity (based on per-hour rate)
        if self._should_perform_activity(pattern.email_per_hour):
            await self._send_email(worker)

        # Teams activity
        if self._should_perform_activity(pattern.teams_messages_per_hour):
            await self._send_teams_message(worker)

        # Document activity (less frequent)
        if self._should_perform_activity(pattern.documents_per_day / 8):  # Spread across 8 hours
            await self._create_document(worker)

    async def _send_email(self, worker: WorkerIdentity) -> None:
        """Send an email as the worker.

        Uses EmailGenerator for content if available, otherwise logs
        a generic email activity.
        """
        subject = None

        if self._email_generator:
            try:
                generated = await self._email_generator.generate(
                    department=worker.department.value,
                    worker_name=worker.display_name,
                )
                subject = generated.subject
            except Exception as e:
                self._log(f"Email generation failed for {worker.display_name}: {e}", "WARNING")

        # In real implementation, use Graph API to send email with subject/body
        activity = {
            "type": "email",
            "worker_id": worker.worker_id,
            "timestamp": datetime.utcnow().isoformat(),
            "subject": subject,
        }

        self._activity_count += 1
        if subject:
            self._log(f'Email sent by {worker.display_name}: "{subject}"')
        else:
            self._log(f"Email sent by {worker.display_name}")

        if self._on_activity:
            self._on_activity(activity)

    async def _send_teams_message(self, worker: WorkerIdentity) -> None:
        """Send a Teams message as the worker."""
        activity = {
            "type": "teams_message",
            "worker_id": worker.worker_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._activity_count += 1
        self._log(f"Teams message sent by {worker.display_name}")

        if self._on_activity:
            self._on_activity(activity)

    async def _create_document(self, worker: WorkerIdentity) -> None:
        """Create a document as the worker."""
        activity = {
            "type": "document",
            "worker_id": worker.worker_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._activity_count += 1
        self._log(f"Document created by {worker.display_name}")

        if self._on_activity:
            self._on_activity(activity)

    def _should_perform_activity(self, per_hour_rate: float) -> bool:
        """Determine if activity should be performed based on rate."""
        import random

        # Convert to probability per minute (since we run every minute)
        probability = per_hour_rate / 60
        return random.random() < probability
