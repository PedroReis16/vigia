package main

import (
	"encoding/binary"
	"io"
	"log"
	"net"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var (
	// Configura o WebSocket permitindo qualquer origem (CORS)
	upgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
	// Canal para transmitir os frames do TCP para o WebSocket
	frameStream = make(chan []byte, 10)
)

func main() {
	// Inicia o listener TCP em uma Goroutine separada para não travar o Gin
	go startTCPServer()

	r := gin.Default()

	// Rota do WebSocket para o Angular consumir
	r.GET("/stream", func(c *gin.Context) {
		ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			log.Println("Erro no upgrade WS:", err)
			return
		}
		defer ws.Close()

		for {
			// Aguarda um novo frame chegar do Python
			frame := <-frameStream
			
			// Envia o frame em formato binário para o Angular
			err = ws.WriteMessage(websocket.BinaryMessage, frame)
			if err != nil {
				log.Println("Cliente desconectado")
				break
			}
		}
	})

	log.Println("Servidor Gin rodando na porta 8091...")
	r.Run(":8091")
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

		// 3. Joga a imagem no canal. Se o canal estiver cheio, descarta para evitar gargalo e lag
		select {
		case frameStream <- frameBuf:
		default:
		}
	}
}