"""Entra ID user management for knowledge workers."""

import secrets
import string
from typing import Callable, Awaitable

from ..models.worker import WorkerConfig, WorkerIdentity


class EntraUserManager:
    """Manages Entra ID users for knowledge workers.

    Creates, tracks, and deletes worker identities in Azure AD.
    """

    def __init__(
        self,
        deployment_id: str,
        get_credential: Callable[[str], Awaitable[str | None]],
    ) -> None:
        """Initialize the user manager.

        Args:
            deployment_id: ID of the parent deployment
            get_credential: Async function to retrieve credentials
        """
        self.deployment_id = deployment_id
        self._get_credential = get_credential
        self._workers: dict[str, WorkerIdentity] = {}
        self._graph_client = None

    async def _get_graph_client(self):
        """Get or create the Microsoft Graph client."""
        if self._graph_client is None:
            # Get credentials from platform
            tenant_id = await self._get_credential("KW_TENANT_ID")
            client_id = await self._get_credential("KW_APP_ID")
            client_secret = await self._get_credential("KW_CLIENT_SECRET")

            if not all([tenant_id, client_id, client_secret]):
                raise ValueError(
                    "Missing M365 credentials. Required: KW_TENANT_ID, KW_APP_ID, KW_CLIENT_SECRET"
                )

            # Initialize Graph client
            # In real implementation:
            # from azure.identity import ClientSecretCredential
            # from msgraph import GraphServiceClient
            # credential = ClientSecretCredential(tenant_id, client_id, client_secret)
            # self._graph_client = GraphServiceClient(credential)

            # Placeholder for now
            self._graph_client = {
                "tenant_id": tenant_id,
                "client_id": client_id,
            }

        return self._graph_client

    async def create_worker(self, config: WorkerConfig) -> WorkerIdentity:
        """Create a new worker identity in Entra ID.

        Args:
            config: Worker configuration

        Returns:
            Created WorkerIdentity
        """
        await self._get_graph_client()

        # Generate UPN
        worker_name = f"haymaker-{config.deployment_id}-{config.worker_number}"
        domain = config.domain or "contoso.onmicrosoft.com"
        upn = f"{worker_name}@{domain}"

        # Generate password for Entra user creation
        self._generate_password()

        # TODO(graph-api): Replace with real Graph API user creation
        # once msgraph-sdk integration is complete
        entra_object_id = f"entra-{worker_name}"

        # Create worker identity
        worker = WorkerIdentity.from_config(
            config=config,
            entra_object_id=entra_object_id,
            upn=upn,
        )

        self._workers[worker.worker_id] = worker
        return worker

    async def delete_worker(self, worker_id: str) -> bool:
        """Delete a worker from Entra ID.

        Args:
            worker_id: ID of worker to delete

        Returns:
            True if deleted successfully
        """
        worker = self._workers.get(worker_id)
        if not worker:
            return False

        await self._get_graph_client()

        # TODO(graph-api): Replace with real Graph API user deletion

        del self._workers[worker_id]
        return True

    async def delete_all_workers(self) -> int:
        """Delete all workers created by this manager.

        Returns:
            Number of workers deleted
        """
        count = 0
        worker_ids = list(self._workers.keys())

        for worker_id in worker_ids:
            if await self.delete_worker(worker_id):
                count += 1

        return count

    def get_workers(self) -> list[WorkerIdentity]:
        """Get all created workers."""
        return list(self._workers.values())

    def _generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))
