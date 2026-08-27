# Build vigia-web (Angular) — context = monorepo root
FROM node:22-alpine AS build
WORKDIR /app

ARG NG_CONFIGURATION=production

RUN corepack enable && corepack prepare pnpm@11.22.0 --activate

COPY vigia-web/package.json vigia-web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY vigia-web/ ./
RUN pnpm exec ng build --configuration="$NG_CONFIGURATION"

# Runtime — static SPA via nginx
FROM nginx:1.27-alpine AS final

COPY docker-compose/dockerfiles/vigia-web.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/vigia-web/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
