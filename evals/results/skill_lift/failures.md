# Failure cases

## lift-hours-range-01 / baseline / seed=1
- exit_status: `Submitted`
- skills loaded: []
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 0}
```
e/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-eyh1xz1a'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-gigzyco4'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_hidden - assert True is False
1 failed, 2 warnings in 0.03s

```

## lift-hours-range-01 / baseline / seed=2
- exit_status: `TimeExceeded`
- skills loaded: []
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 0}
```
e/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-zbej7piw'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-95j8jy1b'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_hidden - assert True is False
1 failed, 2 warnings in 0.03s

```

## lift-hours-range-01 / baseline / seed=3
- exit_status: `TimeExceeded`
- skills loaded: []
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 0}
```
e/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-vlf0fxj5'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-dcxruo8_'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_hidden - assert True is False
1 failed, 2 warnings in 0.02s

```

## lift-hours-range-01 / mcp_only / seed=1
- exit_status: `Submitted`
- skills loaded: []
- mcp: {'ok': 0, 'denied': 0, 'error': 10, 'total': 10, 'cli_mentions': 5}
```
e/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-cfmsl7_i'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-2tlbmnlj'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_hidden - assert True is False
1 failed, 2 warnings in 0.03s

```

