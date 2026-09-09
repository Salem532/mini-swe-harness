# Default Hub name. On hosts that cannot reach docker.io, pass a mirror, e.g.
#   docker build --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim ...
ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash agent

WORKDIR /opt/harness
COPY pyproject.toml README.md /opt/harness/
COPY src /opt/harness/src
COPY .agents /opt/harness/.agents
COPY config /opt/harness/config

RUN pip install --no-cache-dir /opt/harness \
    && mkdir -p /workspace \
    && chown -R 1000:1000 /workspace /opt/harness

ENV PATH="/usr/local/bin:${PATH}" \
    MINI_SWE_HARNESS_ROOT=/opt/harness \
    PYTHONUNBUFFERED=1

USER 1000
WORKDIR /workspace
CMD ["sleep", "infinity"]
