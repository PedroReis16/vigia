import { Component, OnDestroy, OnInit, signal } from '@angular/core';

/**
 * Produção: mesmo host da página + /stream (Traefik → vigia-stream).
 * Dev (ng serve em :4200, etc.): o Gin escuta em :8091 — não usar a porta da página.
 */
function streamWebSocketUrl(): string {
  const loc = globalThis.location;
  if (!loc) {
    return 'ws://127.0.0.1:8091/stream';
  }
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  const h = loc.hostname;
  const isLocalHost = h === 'localhost' || h === '127.0.0.1';
  const streamOnSameOrigin = loc.port === '8091';
  if (isLocalHost && !streamOnSameOrigin) {
    return `${proto}//${h}:8091/stream`;
  }
  return `${proto}//${loc.host}/stream`;
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
