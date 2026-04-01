import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
} from '@angular/core';

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
export class MonitorVigiaComponent implements AfterViewInit, OnDestroy {
  @ViewChild('feedCanvas') feedCanvas?: ElementRef<HTMLCanvasElement>;

  private ws?: WebSocket;
  private ctx?: CanvasRenderingContext2D | null;
  private rafId = 0;
  /** Último frame recebido; durante decode pode ser substituído por um mais novo. */
  private pendingFrame: ArrayBuffer | null = null;
  private paintScheduled = false;
  private destroyed = false;

  ngAfterViewInit(): void {
    const el = this.feedCanvas?.nativeElement;
    if (el) {
      this.ctx = el.getContext('2d');
    }
    this.connectStream();
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    if (this.rafId !== 0) {
      cancelAnimationFrame(this.rafId);
      this.rafId = 0;
    }
    this.pendingFrame = null;
    this.ws?.close();
  }

  private connectStream(): void {
    this.ws = new WebSocket(streamWebSocketUrl());
    this.ws.binaryType = 'arraybuffer';

    this.ws.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      if (this.destroyed) {
        return;
      }
      this.pendingFrame = event.data;
      this.schedulePaint();
    };

    this.ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
    };
  }

  private schedulePaint(): void {
    if (this.paintScheduled || this.destroyed) {
      return;
    }
    this.paintScheduled = true;
    this.rafId = requestAnimationFrame(() => void this.paint());
  }

  private async paint(): Promise<void> {
    this.paintScheduled = false;
    this.rafId = 0;

    const buf = this.pendingFrame;
    if (!buf || this.destroyed || !this.feedCanvas) {
      return;
    }
    if (!this.ctx) {
      this.ctx = this.feedCanvas.nativeElement.getContext('2d');
    }
    if (!this.ctx) {
      return;
    }

    const canvas = this.feedCanvas.nativeElement;
    const blob = new Blob([buf], { type: 'image/jpeg' });

    try {
      const bmp = await createImageBitmap(blob);
      if (this.destroyed) {
        bmp.close();
        return;
      }
      if (canvas.width !== bmp.width || canvas.height !== bmp.height) {
        canvas.width = bmp.width;
        canvas.height = bmp.height;
      }
      this.ctx.drawImage(bmp, 0, 0);
      bmp.close();
    } catch {
      // Frame inválido ou decode indisponível — descarta.
    }

    if (this.pendingFrame === buf) {
      this.pendingFrame = null;
    }
    if (this.pendingFrame !== null && !this.destroyed) {
      this.schedulePaint();
    }
  }
}
