package main

import (
	"encoding/binary"
	"io"
	"log"
	"net"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

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
	// Inicia o listener TCP em uma Goroutine separada para não travar o Gin
	go startTCPServer()
	go fanOutFrames()

	r := gin.Default()

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

	log.Println("Servidor Gin rodando na porta 8091...")
	r.Run(":8091")
}

func fanOutFrames() {
	for frame := range frameStream {
		broadcastFrame(frame)
	}
}

// Escuta a conexão vinda do Python (Placa)
func startTCPServer() {
	l, err := net.Listen("tcp", ":8090")
	if err != nil {
		log.Fatal("Erro ao iniciar TCP:", err)
	}
	defer l.Close()

	log.Println("Aguardando câmera na porta TCP 8090...")
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

		// 3. Copia para o canal: o consumidor faz broadcast a todos os WebSockets.
		// Se o canal estiver cheio, descarta para evitar gargalo e lag.
		select {
		case frameStream <- append([]byte(nil), frameBuf...):
		default:
		}
	}
}