"""Email generation prompt templates.

Public API (the "studs"):
    EMAIL_SYSTEM_PROMPT: System prompt for email generation
    build_email_prompt: Build a user prompt for email generation
"""

EMAIL_SYSTEM_PROMPT = """You are a corporate email writer generating realistic internal business emails.
Write natural-sounding emails that an employee would send during their work day.
Keep emails concise (2-5 sentences for the body).
Include appropriate greetings and sign-offs.
Do not include any markers, tags, or metadata - just the email content."""


def build_email_prompt(
    department: str,
    worker_name: str,
    directive: str | None = None,
) -> str:
    """Build a user prompt for email generation.

    Args:
        department: Worker's department (e.g., "engineering", "sales")
        worker_name: Display name of the worker
        directive: Optional custom directive for email content

    Returns:
        Formatted prompt string
    """
    base = (
        f"Write a short internal business email from {worker_name} in the {department} department."
    )

    if directive:
        base += f"\n\nAdditional context: {directive}"
    else:
        topics = {
            "engineering": "about a code review, sprint update, or technical decision",
            "sales": "about a client meeting, deal progress, or quarterly targets",
            "hr": "about a policy update, onboarding, or team event",
            "finance": "about budget review, expense report, or financial planning",
            "operations": "about process improvement, vendor coordination, or logistics",
            "executive": "about strategic initiative, board preparation, or organizational update",
        }
        topic = topics.get(department.lower(), "about a work-related topic")
        base += f"\nThe email should be {topic}."

    base += (
        "\n\nReturn ONLY the email content (subject line on first line, then body). No other text."
    )
    return base


__all__ = ["EMAIL_SYSTEM_PROMPT", "build_email_prompt"]
