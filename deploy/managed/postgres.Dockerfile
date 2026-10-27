FROM pgvector/pgvector:0.8.2-pg16-bookworm@sha256:00ba258a66dac104fd5171074a0084462a64a1369d8513f3d0a634e2f24d15bc
RUN apt-get update \
    && apt-get install -y --no-install-recommends pgbackrest=2.60.0-1.pgdg12+1 \
    && install -d -m 0755 /etc/pgbackrest \
    && rm -rf /var/lib/apt/lists/*
