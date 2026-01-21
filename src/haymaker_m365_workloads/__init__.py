"""Haymaker M365 Workloads - Knowledge Worker simulation.

This workload package simulates realistic Microsoft 365 knowledge
workers performing everyday activities:
    - Email communication
    - Microsoft Teams messaging
    - Calendar events and meetings
    - Document collaboration (OneDrive, SharePoint)

Workers are organized into departments with distinct activity patterns.
"""

from .workload import M365KnowledgeWorkerWorkload

__version__ = "0.1.0"

__all__ = [
    "M365KnowledgeWorkerWorkload",
    "__version__",
]
