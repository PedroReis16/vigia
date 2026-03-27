package main

import (
	"context"
	
	"log"
	
	"sync"
	"time"

	
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	var wg sync.WaitGroup
	// rotina paralela de processamento
	wg.Add(1)
	
	startWorker := func(name string, interval time.Duration) {
		wg.Add(1)
		go func() {
			defer wg.Done()
			ticker := time.NewTicker(interval)
			defer ticker.Stop()
			for {
				select {
				case <-ctx.Done():
					log.Printf("%s finalizado", name)
					return
				case <-ticker.C:
					log.Printf("%s executando...", name)
				}
			}
		}()
	}


	startWorker("processo-A", 5*time.Second)
	startWorker("processo-B", 10*time.Second)
	startWorker("processo-C", 30*time.Second)
	
	time.Sleep(25 * time.Second) // exemplo
	cancel()
	wg.Wait()

}

func runProcessor(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second) // intervalo fixo
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			log.Println("Processor finalizado")
			return
		case <-ticker.C:
			log.Println("Executando processamento em background...")
			// sua lógica de processamento aqui
		}
	}
}
