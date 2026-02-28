# ---- Build stage ----
FROM oven/bun:1 AS builder

WORKDIR /app

# Copy dependency files first for layer caching
COPY package.json bun.lock ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Build arguments for NEXT_PUBLIC_* env vars
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build the application
RUN bun run build

# ---- Production stage ----
FROM oven/bun:1-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["bun", "run", "server.js"]
