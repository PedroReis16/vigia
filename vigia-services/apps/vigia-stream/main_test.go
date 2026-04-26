package main

import (
	"os"
	"testing"
	"time"
)

func TestResolveListenAddr(t *testing.T) {
	const envKey = "VIGIA_STREAM_TEST_ADDR"
	const fallback = "127.0.0.1:8099"

	oldValue, hadOld := os.LookupEnv(envKey)
	t.Cleanup(func() {
		if hadOld {
			_ = os.Setenv(envKey, oldValue)
			return
		}
		_ = os.Unsetenv(envKey)
	})

	_ = os.Unsetenv(envKey)
	if got := resolveListenAddr(envKey, fallback); got != fallback {
		t.Fatalf("esperado fallback quando env vazio: got=%q want=%q", got, fallback)
	}

	_ = os.Setenv(envKey, "0.0.0.0:8100")
	if got := resolveListenAddr(envKey, fallback); got != "0.0.0.0:8100" {
		t.Fatalf("esperado valor da env válido: got=%q want=%q", got, "0.0.0.0:8100")
	}

	_ = os.Setenv(envKey, "addr-invalido")
	if got := resolveListenAddr(envKey, fallback); got != fallback {
		t.Fatalf("esperado fallback quando env inválido: got=%q want=%q", got, fallback)
	}
}

func TestEnqueueFrameCopiesPayload(t *testing.T) {
	frameStream = make(chan []byte, 1)
	input := []byte{1, 2, 3}

	enqueueFrame(input)
	input[0] = 9

	select {
	case got := <-frameStream:
		if len(got) != 3 || got[0] != 1 {
			t.Fatalf("frame enfileirado não preservou cópia: got=%v", got)
		}
	case <-time.After(500 * time.Millisecond):
		t.Fatal("timeout aguardando frame enfileirado")
	}
}
