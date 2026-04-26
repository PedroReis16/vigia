import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';

import { MonitorVigiaComponent } from './monitor-vigia.component';

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  binaryType = '';
  onmessage: ((event: MessageEvent<ArrayBuffer>) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  close = vi.fn();

  constructor(public readonly url: string) {
    MockWebSocket.instances.push(this);
  }
}

describe('MonitorVigiaComponent', () => {
  let fixture: ComponentFixture<MonitorVigiaComponent>;
  let component: MonitorVigiaComponent;
  let originalWebSocket: typeof WebSocket;
  let originalRequestAnimationFrame: typeof requestAnimationFrame;
  let originalCancelAnimationFrame: typeof cancelAnimationFrame;
  let getContextSpy: ReturnType<typeof vi.spyOn>;
  let requestAnimationFrameSpy: ReturnType<typeof vi.fn>;
  let cancelAnimationFrameSpy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    originalWebSocket = globalThis.WebSocket;
    originalRequestAnimationFrame = globalThis.requestAnimationFrame;
    originalCancelAnimationFrame = globalThis.cancelAnimationFrame;
    globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
    MockWebSocket.instances = [];

    getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue({ drawImage: vi.fn() } as unknown as CanvasRenderingContext2D);

    requestAnimationFrameSpy = vi.fn(() => 123);
    cancelAnimationFrameSpy = vi.fn();
    globalThis.requestAnimationFrame = requestAnimationFrameSpy as unknown as typeof requestAnimationFrame;
    globalThis.cancelAnimationFrame = cancelAnimationFrameSpy as unknown as typeof cancelAnimationFrame;

    await TestBed.configureTestingModule({
      imports: [MonitorVigiaComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(MonitorVigiaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket;
    globalThis.requestAnimationFrame = originalRequestAnimationFrame;
    globalThis.cancelAnimationFrame = originalCancelAnimationFrame;
    getContextSpy.mockRestore();
  });

  it('should create and render monitor title', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(component).toBeTruthy();
    expect(compiled.querySelector('h2')?.textContent).toContain('Monitoramento em tempo real');
  });

  it('should open websocket stream on init', () => {
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0]?.url).toContain('/stream');
    expect(MockWebSocket.instances[0]?.binaryType).toBe('arraybuffer');
    expect(getContextSpy).toHaveBeenCalledWith('2d');
  });

  it('should schedule frame paint when a message arrives', () => {
    const ws = MockWebSocket.instances[0];
    const data = new ArrayBuffer(8);
    const callsBeforeMessage = requestAnimationFrameSpy.mock.calls.length;

    ws?.onmessage?.({ data } as MessageEvent<ArrayBuffer>);

    expect(requestAnimationFrameSpy.mock.calls.length).toBe(callsBeforeMessage + 1);
    expect((component as unknown as { pendingFrame: ArrayBuffer | null }).pendingFrame).toBe(data);
  });

  it('should close websocket and cancel pending frame on destroy', () => {
    (component as unknown as { rafId: number }).rafId = 7;
    const ws = MockWebSocket.instances[0];

    component.ngOnDestroy();

    expect(cancelAnimationFrameSpy).toHaveBeenCalledWith(7);
    expect(ws?.close).toHaveBeenCalledTimes(1);
    expect((component as unknown as { pendingFrame: ArrayBuffer | null }).pendingFrame).toBeNull();
  });
});
