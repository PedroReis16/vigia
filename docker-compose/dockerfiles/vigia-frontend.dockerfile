# Build the Angular application (build context must be the repository root)
FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
# Image ships npm 10; project uses npm 11 — align so `npm ci` matches the lockfile
RUN npm install -g npm@11.6.2 && npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

RUN apk update && apk upgrade --no-cache

COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# SPA fallback for Angular Router
RUN rm /etc/nginx/conf.d/default.conf && \
  printf '%s\n' \
  'server {' \
  '  listen 80;' \
  '  server_name localhost;' \
  '  root /usr/share/nginx/html;' \
  '  index index.html;' \
  '  location / {' \
  '    try_files $uri $uri/ /index.html;' \
  '  }' \
  '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
