# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_middleware.py::test_loads_empty_session

# Lint and format
uv run ruff check starsessions tests
uv run ruff format starsessions tests

# Type check
uv run mypy starsessions tests
```

## Architecture

**starsessions** is a session management library for Starlette/FastAPI. The core flow:

1. `SessionMiddleware` (middleware.py) wraps the ASGI app, reads the session cookie, loads session data from a store, attaches a `SessionHandler` to `request.session`, then persists or deletes it on response.

2. `SessionHandler` (session.py) is the runtime session object stored at `request.session`. It wraps a dict of data plus `SessionMetadata` (created time, lifetime, expiry). Direct manipulation utilities like `load_session()`, `regenerate_session_id()`, and `get_session_id()` operate on this object.

3. `SessionStore` (stores/base.py) is an abstract async interface implemented by three backends:
   - `InMemoryStore` — dict-backed, for tests
   - `CookieStore` — itsdangerous-signed client-side data
   - `RedisStore` — server-side Redis storage

4. `Serializer` (serializers.py) handles encoding/decoding session data; default is `JsonSerializer`.

5. `SessionAutoloadMiddleware` (middleware.py) is an optional second middleware that auto-loads sessions for matching paths, so the inner app doesn't have to call `load_session()` manually.

**Sessions are lazy by default** — data is not loaded from the store until `load_session()` is explicitly awaited (or `SessionAutoloadMiddleware` triggers it). Accessing `request.session` before loading raises `SessionNotLoaded` via `LoadGuard`.

Rolling sessions extend the session TTL on every response when `rolling=True` in the middleware config.

## Commiting

- When i ask you to commit changes, commit them and use `gh` tool to monitor the workflow. I want it green.
- when you do changes to github workflows, use `act` tool to execute workflows on this machine. IMPROTANT: Do not execute publish workflow!

# Releasing
- when i ask you to release a new version, tag and  push changes, then create a new release using `gh` tool. Monitor the deployment using `act tool until it is green.
