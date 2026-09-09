from __future__ import annotations

import time

import pytest
from minisweagent.exceptions import TimeExceeded

from mini_swe_harness.runner import WallBoundModel


class _Cfg:
    def __init__(self) -> None:
        self.model_kwargs = {"timeout": 600, "num_retries": 9}


class _Inner:
    def __init__(self) -> None:
        self.config = _Cfg()
        self.seen: list[dict] = []

    def query(self, messages, **kwargs):
        self.seen.append(dict(self.config.model_kwargs))
        return {"role": "assistant", "content": "ok"}


def test_wall_bound_caps_http_timeout() -> None:
    inner = _Inner()
    wrapped = WallBoundModel(inner, wall_s=30, started_at=time.time())
    wrapped.query([])
    assert inner.seen[0]["timeout"] <= 30
    assert inner.seen[0]["num_retries"] == 0
    assert inner.config.model_kwargs["timeout"] == 600


def test_wall_bound_raises_when_expired() -> None:
    inner = _Inner()
    wrapped = WallBoundModel(inner, wall_s=5, started_at=time.time() - 20)
    with pytest.raises(TimeExceeded):
        wrapped.query([])
    assert inner.seen == []


class _TimeoutInner:
    def __init__(self) -> None:
        self.config = _Cfg()

    def query(self, messages, **kwargs):
        raise TimeoutError("Request timed out")


def test_wall_bound_maps_http_timeout_to_time_exceeded() -> None:
    wrapped = WallBoundModel(_TimeoutInner(), wall_s=30, started_at=time.time())
    with pytest.raises(TimeExceeded):
        wrapped.query([])
