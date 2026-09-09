# Failure cases

## mcp-discount-01 / baseline / seed=1
- exit_status: `Submitted`
- skills loaded: []
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 0}
```
cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-3_0ujkhe'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-116ws61i'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_rules - AssertionError: assert 1.0 =...
1 failed, 2 warnings in 0.03s

```

## mcp-discount-01 / baseline / seed=2
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 5}
```
ace/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-l_5i38bv'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-jfq3ub3g'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_rules - NotImplementedError
1 failed, 2 warnings in 0.02s

```

## mcp-discount-01 / baseline / seed=3
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 4}
```
ace/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-w_reb5ki'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-afjf3y3f'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_rules - NotImplementedError
1 failed, 2 warnings in 0.02s

```

## mcp-discount-01 / skill_only / seed=1
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 7}
```
ace/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-6ewd6hvm'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-kp6gyl2i'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_rules - NotImplementedError
1 failed, 2 warnings in 0.03s

```

