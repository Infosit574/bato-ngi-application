from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Visibility(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    COMMUNITY = "community"


class MemoryKind(StrEnum):
    EPHEMERAL = "ephemeral"
    CONTEXTUAL = "contextual"
    PERSISTENT = "persistent"


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    community_id: UUID
    group_ids: frozenset[UUID] = frozenset()


@dataclass(frozen=True)
class Topic:
    id: UUID
    community_id: UUID
    owner_id: UUID
    name: str
    visibility: Visibility = Visibility.PRIVATE
    group_id: UUID | None = None
    parent_id: UUID | None = None


@dataclass(frozen=True)
class Memory:
    id: UUID
    topic: Topic
    content: str
    kind: MemoryKind


@dataclass(frozen=True)
class ProviderRequest:
    text: str
    allow_cloud: bool = False
