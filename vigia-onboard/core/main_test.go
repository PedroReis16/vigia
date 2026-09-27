package main

import (
	"context"
	"errors"
	"testing"
	"time"

	zmq4 "github.com/go-zeromq/zmq4"
)

func TestRun_CancelaContexto_DuranteDial(t *testing.T) {
	const testEndpoint = "tcp://127.0.0.1:15556"

	ctx, cancel := context.WithCancel(context.Background())
	errCh := make(chan error, 1)
	go func() {
		errCh <- run(ctx, testEndpoint)
	}()

	time.Sleep(100 * time.Millisecond)
	cancel()

	select {
	case err := <-errCh:
		if err != nil && !errors.Is(err, context.Canceled) {
			t.Fatalf("run: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("run não encerrou após cancelar o contexto durante o Dial")
	}
}

func TestRun_CancelaContexto_AposConectar(t *testing.T) {
	const testEndpoint = "tcp://127.0.0.1:15557"

	pub := zmq4.NewPub(context.Background())
	if err := pub.Listen(testEndpoint); err != nil {
		t.Fatalf("subir publisher de teste: %v", err)
	}
	defer pub.Close()

	ctx, cancel := context.WithCancel(context.Background())
	errCh := make(chan error, 1)
	go func() {
		errCh <- run(ctx, testEndpoint)
	}()

	select {
	case err := <-errCh:
		cancel()
		t.Fatalf("run encerrou antes do cancelamento: %v", err)
	case <-time.After(300 * time.Millisecond):
	}

	cancel()

	select {
	case err := <-errCh:
		if err != nil && !errors.Is(err, context.Canceled) {
			t.Fatalf("run: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("run não encerrou após cancelar o contexto")
	}
}
