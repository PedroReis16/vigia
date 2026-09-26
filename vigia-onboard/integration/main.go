package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// Função executada quando uma mensagem chega no tópico assinado
var messagePubHandler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("Recebido na mensagem do tópico: %s\n", msg.Topic())
	fmt.Printf("Payload: %s\n", string(msg.Payload()))
}

// Callback de conexão bem-sucedida
var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Conectado com sucesso ao broker MQTT!")
}

// Callback de perda de conexão
var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Conexão perdida: %v\n", err)
}


func main() {
	// TODO: Configurar a inicialização do broker MQTT conforme a configuração do dispositivo
	broker := "tcp://localhost:1883"
	clientId := "vigia-integration"

	opts := mqtt.NewClientOptions()
	opts.AddBroker(broker)
	opts.SetClientID(clientId)
	opts.SetDefaultPublishHandler(messagePubHandler)
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler

	// Se o seu broker exigir usuário e senha, descomente abaixo:
	// opts.SetUsername("seu_usuario")
	// opts.SetPassword("sua_senha")

	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("Erro ao conectar ao broker: %v", token.Error())
	}

	// Tópico que você deseja escutar/consumir
	topic := "seu/topico/exemplo/#" // O '#' pega sub-tópicos se suportado, ou use um tópico fixo
	qos := byte(1)

	if token := client.Subscribe(topic, qos, nil); token.Wait() && token.Error() != nil {
		log.Fatalf("Erro ao se inscrever no tópico: %v", token.Error())
	}
	fmt.Printf("Inscrito no tópico: %s\n", topic)

	// Mantém o programa rodando até receber um sinal de interrupção (Ctrl+C)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	client.Disconnect(250)
	fmt.Println("Cliente desconectado.")
}
