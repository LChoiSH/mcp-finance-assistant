"""Storage-layer models. The disclosure row reuses clients.dart.Disclosure."""
from __future__ import annotations

from pydantic import BaseModel


class MissingRange(BaseModel):
    """A contiguous YYYYMMDD range absent from the cache for some corp."""

    bgn_de: str
    end_de: str
