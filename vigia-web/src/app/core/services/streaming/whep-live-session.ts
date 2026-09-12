export type WhepLiveStatus = 'connecting' | 'playing' | 'error';

export interface WhepLiveSessionState {
  status: WhepLiveStatus;
  errorMessage: string | null;
  isPaused: boolean;
  isClosed: boolean;
  remoteStream: MediaStream | null;
}

type StateListener = (state: WhepLiveSessionState) => void;

/**
 * Manages a receive-only WHEP session against MediaMTX.
 * Port of vigia_ui/lib/data/services/whep_live_session.dart.
 */
export class WhepLiveSession {
  private whepUrl: string;
  private status: WhepLiveStatus = 'connecting';
  private errorMessage: string | null = null;
  private isPaused = false;
  private isClosedFlag = false;
  private remoteStream: MediaStream | null = null;
  private peerConnection: RTCPeerConnection | null = null;
  private connectGeneration = 0;
  private listeners = new Set<StateListener>();

  constructor(whepUrl: string) {
    this.whepUrl = whepUrl;
  }

  getState(): WhepLiveSessionState {
    return {
      status: this.status,
      errorMessage: this.errorMessage,
      isPaused: this.isPaused,
      isClosed: this.isClosedFlag,
      remoteStream: this.remoteStream,
    };
  }

  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    listener(this.getState());
    return () => this.listeners.delete(listener);
  }

  beginConnecting(): void {
    if (this.isClosedFlag) {
      return;
    }
    this.status = 'connecting';
    this.errorMessage = null;
    this.isPaused = false;
    this.notify();
  }

  markError(error: unknown): void {
    if (this.isClosedFlag) {
      return;
    }
    this.status = 'error';
    this.errorMessage = error instanceof Error ? error.message : String(error);
    this.notify();
  }

  async connect(
    maxAttempts = 24,
    initialDelayMs = 500,
    maxDelayMs = 5000,
  ): Promise<void> {
    if (this.isClosedFlag) {
      return;
    }

    const generation = ++this.connectGeneration;
    this.beginConnecting();

    let delayMs = initialDelayMs;
    let lastError: unknown = null;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      if (this.isClosedFlag || generation !== this.connectGeneration) {
        return;
      }

      try {
        await this.negotiate();
        if (this.isClosedFlag || generation !== this.connectGeneration) {
          return;
        }
        this.status = 'playing';
        this.errorMessage = null;
        this.notify();
        return;
      } catch (error) {
        lastError = error;
        await this.teardownPeer();
        if (this.isClosedFlag || generation !== this.connectGeneration) {
          return;
        }
        if (attempt === maxAttempts - 1) {
          break;
        }
        await this.delay(delayMs);
        delayMs = Math.min(delayMs * 2, maxDelayMs);
      }
    }

    if (this.isClosedFlag || generation !== this.connectGeneration) {
      return;
    }
    this.markError(lastError ?? 'Failed to connect to live stream');
  }

  togglePause(): void {
    const stream = this.remoteStream;
    if (!stream || this.status !== 'playing') {
      return;
    }

    this.isPaused = !this.isPaused;
    for (const track of stream.getVideoTracks()) {
      track.enabled = !this.isPaused;
    }
    for (const track of stream.getAudioTracks()) {
      track.enabled = !this.isPaused;
    }
    this.notify();
  }

  async close(): Promise<void> {
    if (this.isClosedFlag) {
      return;
    }
    this.isClosedFlag = true;
    this.connectGeneration++;

    this.status = 'connecting';
    this.errorMessage = null;
    this.isPaused = false;
    this.notify();

    await this.teardownPeer();
    await this.delay(0);
  }

  private async negotiate(): Promise<void> {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });
    this.peerConnection = pc;

    pc.ontrack = (event: RTCTrackEvent) => {
      if (this.isClosedFlag || !event.streams[0]) {
        return;
      }
      this.remoteStream = event.streams[0];
      this.notify();
    };

    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await this.waitForIceGathering(pc);

    const local = pc.localDescription;
    const sdp = local?.sdp;
    if (!sdp) {
      throw new Error('Empty local SDP offer');
    }

    const response = await fetch(this.whepUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/sdp',
        Accept: 'application/sdp',
      },
      body: sdp,
    });

    if (response.status !== 200 && response.status !== 201) {
      throw new Error(`WHEP negotiate failed (${response.status})`);
    }

    const answerSdp = await response.text();
    if (!answerSdp) {
      throw new Error('Empty WHEP SDP answer');
    }

    await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
  }

  private async waitForIceGathering(pc: RTCPeerConnection): Promise<void> {
    if (pc.iceGatheringState === 'complete') {
      return;
    }

    await new Promise<void>((resolve) => {
      const timeout = window.setTimeout(resolve, 8000);
      pc.onicegatheringstatechange = () => {
        if (pc.iceGatheringState === 'complete') {
          window.clearTimeout(timeout);
          resolve();
        }
      };
    });
  }

  private async teardownPeer(): Promise<void> {
    const stream = this.remoteStream;
    this.remoteStream = null;

    if (stream) {
      for (const track of stream.getTracks()) {
        track.stop();
      }
    }

    const pc = this.peerConnection;
    this.peerConnection = null;
    if (pc) {
      pc.close();
    }
  }

  private notify(): void {
    const state = this.getState();
    for (const listener of this.listeners) {
      listener(state);
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }
}
