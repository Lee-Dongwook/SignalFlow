FROM node:20-alpine AS dependencies

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

COPY apps/dashboard/package.json apps/dashboard/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0

RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY --from=dependencies /app/node_modules ./node_modules
COPY apps/dashboard/ ./

RUN pnpm build

EXPOSE 3000

CMD ["sh", "-c", "pnpm start --port ${PORT:-3000}"]
