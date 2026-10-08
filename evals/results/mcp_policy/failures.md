# Failure cases

## policy-deny-01 / baseline / seed=1
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 9}
```
cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-sz7joqre'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-yx727ra2'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_ticket_rules - AssertionError: asser...
1 failed, 2 warnings in 0.02s

```

## policy-deny-01 / baseline / seed=2
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 2}
```
cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-wg4xmo6t'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-bzanv87z'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_ticket_rules - AssertionError: asser...
1 failed, 2 warnings in 0.03s

```

## policy-deny-01 / baseline / seed=3
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 0, 'denied': 0, 'error': 0, 'total': 0, 'cli_mentions': 9}
```
cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-ke6joa3l'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-o8rbe56o'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_ticket_rules - AssertionError: asser...
1 failed, 2 warnings in 0.02s

```

## policy-deny-01 / full / seed=3
- exit_status: `TimeExceeded`
- skills loaded: ['mcp-ticket-context']
- mcp: {'ok': 13, 'denied': 0, 'error': 0, 'total': 13, 'cli_mentions': 16}
```
cache/v/cache/nodeids: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-ry9hpptu'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

../usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423
  /usr/local/lib/python3.12/site-packages/_pytest/cacheprovider.py:423: PytestCacheWarning: could not create cache path /workspace/.pytest_cache/v/cache/lastfailed: [Errno 30] Read-only file system: '/workspace/pytest-cache-files-_6_8i0yq'
    config.cache.set("cache/lastfailed", self.lastfailed)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/hidden/test_hidden.py::test_ticket_rules - AssertionError: asser...
1 failed, 2 warnings in 0.03s

```

