"""Persistent hash cache for incremental deduplication."""

import json
import os
from typing import Set


class HashCache:
    """Simple file-backed SHA256 cache."""

    def __init__(self, path: str):
        """Initialize cache backend.

        :param path: JSON file path.
        """
        self.path = path
        self._hashes: Set[str] = set()
        self._loaded = False

    def load(self) -> Set[str]:
        """Load cache from disk.

        :return: Cached hashes.
        """
        if self._loaded:
            return self._hashes
        self._loaded = True
        if not os.path.exists(self.path):
            self._hashes = set()
            return self._hashes
        with open(self.path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        hashes = payload.get("hashes", [])
        self._hashes = {str(item) for item in hashes}
        return self._hashes

    def add(self, value: str) -> None:
        """Add hash to in-memory set.

        :param value: SHA256 value.
        """
        self._hashes.add(value)

    def contains(self, value: str) -> bool:
        """Check if hash exists.

        :param value: SHA256 value.
        :return: ``True`` when found.
        """
        return value in self._hashes

    def save(self) -> None:
        """Persist cache file."""
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        payload = {"hashes": sorted(self._hashes)}
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
