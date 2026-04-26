# Build vigia-api from modular workspace (vigia-services/apps/vigia-api)
FROM golang:1.26.2-alpine AS builder

WORKDIR /src/vigia-services

# 1) Copia arquivos do modulo da API para aproveitar cache
COPY vigia-services/apps/vigia-api/go.mod vigia-services/apps/vigia-api/go.sum ./apps/vigia-api/

# 2) Copia o código-fonte do serviço
COPY vigia-services/apps/vigia-api/ ./apps/vigia-api/

# 3) Build do binário da API
WORKDIR /src/vigia-services/apps/vigia-api
RUN GOWORK=off CGO_ENABLED=0 go build -p=1 -trimpath -ldflags="-s -w" -o /bin/vigia-api .

# Etapa de execução (imagem final)
FROM alpine:3.22
RUN apk update && apk upgrade --no-cache

WORKDIR /app
COPY --from=builder /bin/vigia-api .
EXPOSE 8000
ENTRYPOINT ["./vigia-api"]