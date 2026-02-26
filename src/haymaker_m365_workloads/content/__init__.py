"""Email content generation module."""
from .email_generator import EmailGenerator
from .prompts import EMAIL_SYSTEM_PROMPT, build_email_prompt

__all__ = ["EmailGenerator", "EMAIL_SYSTEM_PROMPT", "build_email_prompt"]
