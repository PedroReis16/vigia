package main

import (
	"encoding/binary"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

const maxIngestBodyBytes = 8 << 20 // 8 MiB — um JPEG por POST

var (
	// Configura o WebSocket permitindo qualquer origem (CORS)
	upgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
	// Canal: um único consumidor faz fan-out para todos os WebSockets (várias abas/dispositivos).
	frameStream = make(chan []byte, 10)

	subsMu  sync.RWMutex
	clients = make(map[*websocket.Conn]struct{})
)

// resolveListenAddr devolve host:port a partir da env ou o default; rejeita valores que net.ResolveTCPAddr não aceita.
func resolveListenAddr(envKey, defaultAddr string) string {
	v := strings.TrimSpace(os.Getenv(envKey))
	if v == "" {
		v = defaultAddr
	}
	if _, err := net.ResolveTCPAddr("tcp", v); err != nil {
		// #nosec G706 -- valor só vem de env/local; %q no valor cru
		log.Printf("aviso: %s=%q inválido (%v), uso %q", envKey, v, err, defaultAddr)
		return defaultAddr
	}
	return v
}

func registerWS(c *websocket.Conn) {
	subsMu.Lock()
	clients[c] = struct{}{}
	subsMu.Unlock()
}

func unregisterWS(c *websocket.Conn) {
	subsMu.Lock()
	delete(clients, c)
	subsMu.Unlock()
}

func enqueueFrame(frame []byte) {
	select {
	case frameStream <- append([]byte(nil), frame...):
	default:
	}
}

// broadcastFrame envia o mesmo frame a todos os clientes conectados.
func broadcastFrame(frame []byte) {
	payload := append([]byte(nil), frame...)
	subsMu.RLock()
	list := make([]*websocket.Conn, 0, len(clients))
	for c := range clients {
		list = append(list, c)
	}
	subsMu.RUnlock()
	for _, c := range list {
		if err := c.WriteMessage(websocket.BinaryMessage, payload); err != nil {
			log.Println("Falha ao enviar frame para cliente, removendo:", err)
			unregisterWS(c)
			_ = c.Close()
		}
	}
}

func main() {
	const defTCP = "127.0.0.1:8090"
	const defHTTP = "127.0.0.1:8091"
	tcpAddr := resolveListenAddr("VIGIA_STREAM_TCP_ADDR", defTCP)
	httpAddr := resolveListenAddr("VIGIA_STREAM_HTTP_ADDR", defHTTP)

	// Inicia o listener TCP em uma Goroutine separada para não travar o Gin
	go startTCPServer(tcpAddr)
	go fanOutFrames()

	r := gin.Default()

	// POST /ingest — mesmo pipeline que o TCP (Traefik HTTPS :443 → sem porta extra no firewall)
	r.POST("/ingest", func(c *gin.Context) {
		secret := strings.TrimSpace(os.Getenv("VIGIA_INGEST_TOKEN"))
		if secret != "" && c.GetHeader("X-Vigia-Ingest-Token") != secret {
			c.AbortWithStatus(http.StatusUnauthorized)
			return
		}
		body, err := io.ReadAll(io.LimitReader(c.Request.Body, maxIngestBodyBytes+1))
		if err != nil {
			c.AbortWithStatus(http.StatusBadRequest)
			return
		}
		if len(body) == 0 {
			c.AbortWithStatus(http.StatusBadRequest)
			return
		}
		if len(body) > maxIngestBodyBytes {
			c.AbortWithStatus(http.StatusRequestEntityTooLarge)
			return
		}
		enqueueFrame(body)
		c.Status(http.StatusNoContent)
	})

	// Rota do WebSocket para o Angular consumir (múltiplos clientes em paralelo)
	r.GET("/stream", func(c *gin.Context) {
		ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			log.Println("Erro no upgrade WS:", err)
			return
		}
		registerWS(ws)
		defer func() {
			unregisterWS(ws)
			_ = ws.Close()
		}()

		// Lê até o cliente fechar; sem isso o servidor pode não notar desconexão.
		for {
			_, _, err := ws.ReadMessage()
			if err != nil {
				break
			}
		}
	})

	if strings.TrimSpace(os.Getenv("VIGIA_INGEST_TOKEN")) == "" {
		log.Println("aviso: VIGIA_INGEST_TOKEN vazio — POST /ingest aceita qualquer cliente que alcance o Gin (use token em produção).")
	}
	// #nosec G706 -- httpAddr validado por resolveListenAddr
	log.Printf("Servidor Gin em %s (GET /stream, POST /ingest)…", httpAddr)
	if err := r.Run(httpAddr); err != nil {
		log.Fatalf("gin: %v", err)
	}
}

func fanOutFrames() {
	for frame := range frameStream {
		broadcastFrame(frame)
	}
}

// Escuta a conexão vinda do Python (Placa)
func startTCPServer(addr string) {
	l, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatal("Erro ao iniciar TCP:", err)
	}
	defer l.Close()

	// #nosec G706 -- addr validado por resolveListenAddr antes de Listen
	log.Printf("Aguardando câmera em tcp://%s …", addr)
	for {
		conn, err := l.Accept()
		if err != nil {
			continue
		}
		go handleCameraConnection(conn)
	}
}

// Processa o fluxo contínuo de bytes do OpenCV
func handleCameraConnection(conn net.Conn) {
	defer conn.Close()
	log.Println("Câmera conectada!")

	for {
		// 1. Lê os 4 primeiros bytes para descobrir o tamanho do frame
		sizeBuf := make([]byte, 4)
		if _, err := io.ReadFull(conn, sizeBuf); err != nil {
			log.Println("Câmera desconectada")
			return
		}
		size := binary.LittleEndian.Uint32(sizeBuf)

		// 2. Lê exatamente a quantidade de bytes da imagem
		frameBuf := make([]byte, size)
		if _, err := io.ReadFull(conn, frameBuf); err != nil {
			return
		}

		enqueueFrame(frameBuf)
	}
}