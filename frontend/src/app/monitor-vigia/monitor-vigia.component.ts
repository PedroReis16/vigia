import { Component, OnDestroy, OnInit, signal } from '@angular/core';

/** Mesmo host da página + path /stream (Traefik → vigia-stream:8091). Local: ws://localhost:8091/stream */
function streamWebSocketUrl(): string {
  const proto = globalThis.location?.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = globalThis.location?.host ?? '127.0.0.1:8091';
  return `${proto}//${host}/stream`;
}

@Component({
  selector: 'app-monitor-vigia',
  templateUrl: './monitor-vigia.component.html',
  styleUrl: './monitor-vigia.component.css',
})
export class MonitorVigiaComponent implements OnInit, OnDestroy {
  /**
   * Signal: callbacks do WebSocket rodam fora do ciclo normal do Angular (e apps zoneless
   * não re-renderizam); atualizar um signal notifica o template de forma confiável.
   */
  readonly feedSrc = signal('/placeholder.svg');

  private ws?: WebSocket;

  ngOnInit(): void {
    this.connectStream();
  }

  ngOnDestroy(): void {
    this.revokeFeedBlob();
    this.ws?.close();
  }

  private connectStream(): void {
    this.ws = new WebSocket(streamWebSocketUrl());
    this.ws.binaryType = 'arraybuffer';

    this.ws.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      const arrayBuffer = event.data;
      const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });

      this.revokeFeedBlob();
      this.feedSrc.set(URL.createObjectURL(blob));
    };

    this.ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
    };
  }

  private revokeFeedBlob(): void {
    const current = this.feedSrc();
    if (current.startsWith('blob:')) {
      URL.revokeObjectURL(current);
    }
  }
}
