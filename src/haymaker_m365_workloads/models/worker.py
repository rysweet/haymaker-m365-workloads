"""Worker identity and configuration models."""

from enum import Enum
from pydantic import BaseModel, Field


class Department(str, Enum):
    """Worker department types with distinct activity patterns."""

    OPERATIONS = "operations"
    ENGINEERING = "engineering"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    EXECUTIVE = "executive"


class ActivityPattern(BaseModel):
    """Activity pattern configuration for a department."""

    email_per_hour: int = 5
    teams_messages_per_hour: int = 10
    documents_per_day: int = 3
    meetings_per_day: int = 4
    activity_variance_percent: int = 30
    work_start_hour: int = 8  # UTC
    work_end_hour: int = 17  # UTC


# Department-specific activity patterns
DEPARTMENT_PATTERNS: dict[Department, ActivityPattern] = {
    Department.OPERATIONS: ActivityPattern(
        email_per_hour=6,
        teams_messages_per_hour=8,
        documents_per_day=4,
        meetings_per_day=4,
    ),
    Department.ENGINEERING: ActivityPattern(
        email_per_hour=4,
        teams_messages_per_hour=15,
        documents_per_day=6,
        meetings_per_day=3,
    ),
    Department.SALES: ActivityPattern(
        email_per_hour=12,
        teams_messages_per_hour=10,
        documents_per_day=3,
        meetings_per_day=8,
    ),
    Department.HR: ActivityPattern(
        email_per_hour=10,
        teams_messages_per_hour=8,
        documents_per_day=5,
        meetings_per_day=5,
    ),
    Department.FINANCE: ActivityPattern(
        email_per_hour=6,
        teams_messages_per_hour=5,
        documents_per_day=8,
        meetings_per_day=4,
    ),
    Department.EXECUTIVE: ActivityPattern(
        email_per_hour=8,
        teams_messages_per_hour=5,
        documents_per_day=2,
        meetings_per_day=10,
    ),
}


class WorkerConfig(BaseModel):
    """Configuration for creating a new worker."""

    department: Department
    worker_number: int
    deployment_id: str
    display_name_prefix: str = "Haymaker"
    domain: str | None = None  # If None, uses tenant default domain


class WorkerIdentity(BaseModel):
    """A created worker identity in Entra ID."""

    worker_id: str = Field(..., description="Unique worker identifier")
    display_name: str = Field(..., description="Entra display name")
    user_principal_name: str = Field(..., description="UPN for M365 login")
    department: Department
    entra_object_id: str = Field(..., description="Entra ID object ID")
    deployment_id: str
    activity_pattern: ActivityPattern = Field(default_factory=ActivityPattern)

    @classmethod
    def from_config(cls, config: WorkerConfig, entra_object_id: str, upn: str) -> "WorkerIdentity":
        """Create WorkerIdentity from config and Entra response."""
        display_name = f"{config.display_name_prefix} Worker {config.worker_number}"
        worker_id = f"worker-{config.deployment_id}-{config.worker_number}"

        return cls(
            worker_id=worker_id,
            display_name=display_name,
            user_principal_name=upn,
            department=config.department,
            entra_object_id=entra_object_id,
            deployment_id=config.deployment_id,
            activity_pattern=DEPARTMENT_PATTERNS.get(
                config.department, ActivityPattern()
            ),
        )
