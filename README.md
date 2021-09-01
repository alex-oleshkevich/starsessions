# FastAPI Backstage Sesh

## Pluggable session support for FastAPI framework

This is an extension built on top of the strong foundation of `starsession` by Alex Oleshkevich located here on [GitHub: alex-oleshkevich/starsessions](https://github.com/alex-oleshkevich/starsessions)
You can find the work on his Repo to be just as well compatible with your FastAPI App or other Starlette frameworks with ease. This repository will be a work extending on this strong foundation.

## Roadmap

I want to do two things with this project located here on this repository;

1. Add an ease-of-use option for FastAPI's Background Task to share the same Session with User for long computational task.
2. Add Redis Support as a `RedisBackend`

## Installation

Install `fastapi-backstage-sesh` using PIP or poetry:

```bash
pip install fastapi-backstage-sesh
# or
poetry add fastapi-backstage-sesh
```

## Quick start

See example application in `examples/` directory of this repository.

### Run Examples

To run the provided examples, first you must install extra dependencies [uvicorn](https://github.com/encode/uvicorn)
Run the following command to do so

```bash
pip install -e .[examples]
# or
poetry install --extras examples
```
