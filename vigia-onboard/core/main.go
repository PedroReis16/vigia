package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	zmq4 "github.com/go-zeromq/zmq4"
)

const endpoint = "tcp://127.0.0.1:5556"

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if err := run(ctx, endpoint); err != nil && !errors.Is(err, context.Canceled) {
		log.Fatal(err)
	}
	log.Println("Servidor ZeroMQ encerrado")
}

func run(ctx context.Context, pubEndpoint string) error {
	sub := zmq4.NewSub(ctx,
		zmq4.WithDialerTimeout(time.Second),
		zmq4.WithDialerRetry(200*time.Millisecond),
		zmq4.WithDialerMaxRetries(-1),
		zmq4.WithAutomaticReconnect(true),
	)

	var closeOnce sync.Once
	closeSock := func() {
		closeOnce.Do(func() {
			if err := sub.Close(); err != nil {
				log.Printf("Erro ao fechar o socket: %v", err)
			}
		})
	}
	defer closeSock()

	go func() {
		<-ctx.Done()
		closeSock()
	}()

	if err := sub.SetOption(zmq4.OptionSubscribe, ""); err != nil {
		return fmt.Errorf("definir opção de subscrição: %w", err)
	}

	log.Printf("Cliente ZeroMQ SUB a ligar a %s", pubEndpoint)
	if err := sub.Dial(pubEndpoint); err != nil {
		if ctx.Err() != nil {
			return ctx.Err()
		}
		return fmt.Errorf("ligar ao publisher: %w", err)
	}

	for {
		msg, err := sub.Recv()
		if err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			log.Printf("Erro ao receber mensagem: %v", err)
			continue
		}
		if len(msg.Frames) == 0 {
			continue
		}

		fmt.Printf("Servidor recebeu: %s\n", string(msg.Frames[0]))
	}
}
