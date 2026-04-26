# Build vigia-stream from modular workspace (vigia-services/apps/vigia-stream)
FROM golang:1.26.2-alpine AS builder

WORKDIR /src/vigia-services

# 1) Copia arquivos do modulo do stream para aproveitar cache
COPY vigia-services/apps/vigia-stream/go.mod vigia-services/apps/vigia-stream/go.sum ./apps/vigia-stream/

# 2) Copia o código-fonte do serviço
COPY vigia-services/apps/vigia-stream/ ./apps/vigia-stream/

# 3) Build do binário do stream
WORKDIR /src/vigia-services/apps/vigia-stream
RUN GOWORK=off CGO_ENABLED=0 go build -p=1 -trimpath -ldflags="-s -w" -o /bin/vigia-stream .

# Etapa de execução (imagem final)
FROM alpine:latest
RUN apk update && apk upgrade --no-cache

WORKDIR /app
COPY --from=builder /bin/vigia-stream .
EXPOSE 8090 8091
ENTRYPOINT ["./vigia-stream"]