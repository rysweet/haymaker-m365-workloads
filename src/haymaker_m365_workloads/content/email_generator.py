"""LLM-powered email content generation.

Public API (the "studs"):
    EmailGenerator: Generates realistic email content using LLM providers
"""

import logging
from dataclasses import dataclass

from .prompts import EMAIL_SYSTEM_PROMPT, build_email_prompt

logger = logging.getLogger(__name__)


@dataclass
class GeneratedEmail:
    """Generated email content."""

    subject: str
    body: str


class EmailGenerator:
    """Generates realistic email content using LLM providers.

    Falls back to template-based content when LLM is unavailable.
    """

    def __init__(self, llm_client=None, directive: str | None = None):
        """Initialize email generator.

        Args:
            llm_client: Optional BaseLLMProvider instance from agent_haymaker.llm
            directive: Optional custom directive for email generation
        """
        self._llm_client = llm_client
        self._directive = directive
        self._fallback_counter = 0

    @property
    def has_llm(self) -> bool:
        """Whether an LLM client is available."""
        return self._llm_client is not None

    async def generate(self, department: str, worker_name: str) -> GeneratedEmail:
        """Generate an email.

        Uses LLM if available, otherwise falls back to templates.

        Args:
            department: Worker's department
            worker_name: Display name of the worker

        Returns:
            GeneratedEmail with subject and body
        """
        if self._llm_client:
            try:
                return await self._generate_with_llm(department, worker_name)
            except Exception as e:
                logger.warning(f"LLM generation failed, using fallback: {e}")

        return self._generate_fallback(department, worker_name)

    async def _generate_with_llm(self, department: str, worker_name: str) -> GeneratedEmail:
        """Generate email content using LLM."""
        try:
            from agent_haymaker.llm import LLMMessage
        except ImportError:
            logger.warning("agent_haymaker.llm not available, using fallback")
            return self._generate_fallback(department, worker_name)

        prompt = build_email_prompt(department, worker_name, self._directive)
        messages = [LLMMessage(role="user", content=prompt)]

        response = await self._llm_client.create_message_async(
            messages=messages,
            system=EMAIL_SYSTEM_PROMPT,
            max_tokens=500,
            temperature=0.8,
        )

        return self._parse_email_response(response.content, worker_name)

    def _parse_email_response(self, content: str, worker_name: str) -> GeneratedEmail:
        """Parse LLM response into subject and body."""
        lines = content.strip().split("\n", 1)

        if len(lines) >= 2:
            subject = lines[0].strip()
            # Remove common prefixes
            for prefix in ["Subject:", "subject:", "RE:", "Re:"]:
                if subject.startswith(prefix):
                    subject = subject[len(prefix) :].strip()
            body = lines[1].strip()
        else:
            subject = f"Update from {worker_name}"
            body = content.strip()

        return GeneratedEmail(subject=subject, body=body)

    def _generate_fallback(self, department: str, worker_name: str) -> GeneratedEmail:
        """Generate template-based email content."""
        self._fallback_counter += 1
        n = self._fallback_counter

        templates = {
            "engineering": [
                (
                    "Sprint Update",
                    f"Hi team,\n\nJust a quick update on the current sprint. We're on track with the planned deliverables.\n\nBest,\n{worker_name}",
                ),
                (
                    "Code Review Request",
                    f"Hi,\n\nCould you take a look at my latest PR when you get a chance? It addresses the performance issue we discussed.\n\nThanks,\n{worker_name}",
                ),
            ],
            "sales": [
                (
                    "Client Follow-up",
                    f"Hi team,\n\nFollowing up on today's client call. They're interested in moving forward with the proposal.\n\nBest,\n{worker_name}",
                ),
                (
                    "Pipeline Update",
                    f"Hi,\n\nQuick update on the Q4 pipeline - we're tracking well against targets.\n\nRegards,\n{worker_name}",
                ),
            ],
        }

        dept_templates = templates.get(
            department.lower(),
            [
                (
                    "Work Update",
                    f"Hi,\n\nSharing a quick update on current priorities.\n\nBest,\n{worker_name}",
                ),
            ],
        )

        template = dept_templates[n % len(dept_templates)]
        return GeneratedEmail(subject=template[0], body=template[1])


__all__ = ["EmailGenerator", "GeneratedEmail"]
