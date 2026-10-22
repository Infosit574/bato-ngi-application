from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from bato.domain.models import Memory, Principal, ProviderRequest


class Authenticator(Protocol):
    async def authenticate(self, credential: str) -> Principal:
        """Reject invalid credentials; implementations must not log the credential."""
        ...


class MemoryStore(Protocol):
    async def retrieve(self, principal: Principal, topic_id: UUID) -> Sequence[Memory]:
        """Return only memories visible to this principal within their community."""
        ...


class ModelRouter(Protocol):
    async def route(self, request: ProviderRequest) -> str:
        """Select a provider without sending private-only requests outside the node."""
        ...


class Orchestrator(Protocol):
    async def respond(self, principal: Principal, request: ProviderRequest) -> str:
        """Coordinate authorized memory, providers, and confirmed tool actions."""
        ...
