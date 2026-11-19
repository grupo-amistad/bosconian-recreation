from dataclasses import dataclass, field
from typing import Any


@dataclass
class CState:
    """Named gameplay state with elapsed time and optional state data."""

    name: str
    elapsed: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
