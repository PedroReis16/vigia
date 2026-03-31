import {
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';

/** URL do WebSocket do backend (vigia-stream). Ajuste se o host/porta mudarem. */
const STREAM_WS_URL = 'ws://127.0.0.1:8091/stream';

@Component({
  selector: 'app-monitor-vigia',
  templateUrl: './monitor-vigia.component.html',
  styleUrl: './monitor-vigia.component.css',
})
export class MonitorVigiaComponent implements OnInit, OnDestroy {
  @ViewChild('cameraFeed', { static: true })
  cameraFeed!: ElementRef<HTMLImageElement>;

  defaultImage = '/placeholder.svg';

  private ws?: WebSocket;

  ngOnInit(): void {
    this.connectStream();
  }

  ngOnDestroy(): void {
    this.revokeCurrentBlobUrl();
    this.ws?.close();
  }

  private connectStream(): void {
    this.ws = new WebSocket(STREAM_WS_URL);
    this.ws.binaryType = 'arraybuffer';

    this.ws.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      const arrayBuffer = event.data;
      const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });

      this.revokeCurrentBlobUrl();
      this.cameraFeed.nativeElement.src = URL.createObjectURL(blob);
    };

    this.ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
    };
  }

  private revokeCurrentBlobUrl(): void {
    const src = this.cameraFeed?.nativeElement?.src;
    if (src?.startsWith('blob:')) {
      URL.revokeObjectURL(src);
    }
  }
}
