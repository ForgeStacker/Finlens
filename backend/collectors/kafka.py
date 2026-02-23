"""Amazon Managed Kafka (alias) collectors."""
from __future__ import annotations

from .msk import collect_msk as collect_kafka

__all__ = ["collect_kafka"]
