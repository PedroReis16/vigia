import { Component, OnDestroy, OnInit, signal } from '@angular/core';

/**
 * WebSocket do Gin (vigia-stream). A porta 8091 serve HTTP/WS; a 8090 é só TCP da câmera.
 */
const STREAM_WS_URL = 'ws://127.0.0.1:8091/stream';

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
    this.ws = new WebSocket(STREAM_WS_URL);
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
