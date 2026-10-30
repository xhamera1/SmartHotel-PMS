# Multi-stage SPA build → nginx (compose profile app).
FROM node:24-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Empty base URL → browser talks same-origin; nginx proxies /api to pms-core.
ARG VITE_API_BASE_URL=
ARG VITE_LOCALE=pl-PL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL VITE_LOCALE=$VITE_LOCALE
RUN pnpm build

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD wget -qO- http://127.0.0.1/ || exit 1
