FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=7860 \
    NEXT_PUBLIC_API_URL=/ \
    INTERNAL_API_URL=http://127.0.0.1:8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      curl \
      libpq-dev \
      python3 \
      python3-pip \
      python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/node/app

COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web/package.json apps/web/package.json

RUN corepack enable \
    && corepack prepare pnpm@8.15.0 --activate \
    && pnpm install --filter @applymap/web... --frozen-lockfile

COPY --chown=node:node apps/api/requirements.txt apps/api/requirements.txt

RUN python3 -m venv /home/node/venv \
    && /home/node/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /home/node/venv/bin/pip install --no-cache-dir -r apps/api/requirements.txt

COPY --chown=node:node apps/web apps/web
COPY --chown=node:node apps/api apps/api
COPY --chown=node:node start.sh start.sh

RUN chmod +x start.sh \
    && pnpm --filter @applymap/web build \
    && chown -R node:node /home/node/app /home/node/venv

USER node

EXPOSE 7860

CMD ["./start.sh"]
