import { inject, Injectable, OnDestroy } from '@angular/core';
import {
  GroupMembershipChangedDto,
  isDuplicateMembershipEvent,
  membershipEventKey,
  parseGroupMembershipChanged,
} from '@core/entities';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { environment } from '@environments/environment';
import {
  HubConnection,
  HubConnectionBuilder,
  HubConnectionState,
} from '@microsoft/signalr';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class DeviceGroupsRealtimeService implements OnDestroy {
  private readonly session = inject(AuthSessionService);

  private connection: HubConnection | null = null;
  private readonly membershipChangedSubject = new Subject<GroupMembershipChangedDto>();
  private lastMembershipEvent: { key: string; at: number } | null = null;
  private retryHandle: ReturnType<typeof setTimeout> | null = null;
  private stopped = false;

  readonly membershipChanged$ = this.membershipChangedSubject.asObservable();

  ngOnDestroy(): void {
    void this.disconnect();
    this.membershipChangedSubject.complete();
  }

  get isConnected(): boolean {
    return this.connection?.state === HubConnectionState.Connected;
  }

  async connect(): Promise<void> {
    this.stopped = false;
    this.clearRetry();

    const current = this.connection;
    if (
      current &&
      (current.state === HubConnectionState.Connected ||
        current.state === HubConnectionState.Connecting ||
        current.state === HubConnectionState.Reconnecting)
    ) {
      return;
    }

    await this.stopConnection();

    const token = await this.ensureAccessToken();
    if (!token) {
      this.scheduleRetry();
      return;
    }

    const hubUrl = `${environment.apiUrl.replace(/\/$/, '')}/hubs/device-groups`;
    const connection = new HubConnectionBuilder()
      .withUrl(hubUrl, {
        // Bearer token, not cookies. Traefik answers CORS with origin *,
        // which the browser rejects when the negotiate request sends credentials.
        withCredentials: false,
        accessTokenFactory: () => this.ensureAccessToken(),
      })
      .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
      .build();

    connection.on('GroupMembershipChanged', (...args: unknown[]) => {
      const event = parseGroupMembershipChanged(args[0]);
      if (!event) {
        return;
      }

      const now = Date.now();
      if (isDuplicateMembershipEvent(this.lastMembershipEvent, event, now)) {
        return;
      }

      this.lastMembershipEvent = { key: membershipEventKey(event), at: now };
      this.membershipChangedSubject.next(event);
    });

    this.connection = connection;
    try {
      await connection.start();
    } catch (error: unknown) {
      console.error('[SignalR] connect failed', error);
      this.scheduleRetry();
    }
  }

  async disconnect(): Promise<void> {
    this.stopped = true;
    this.clearRetry();
    await this.stopConnection();
  }

  private scheduleRetry(): void {
    if (this.stopped || this.retryHandle != null || typeof setTimeout === 'undefined') {
      return;
    }

    this.retryHandle = setTimeout(() => {
      this.retryHandle = null;
      if (!this.stopped) {
        void this.connect();
      }
    }, 3000);
  }

  private clearRetry(): void {
    if (this.retryHandle == null) {
      return;
    }

    clearTimeout(this.retryHandle);
    this.retryHandle = null;
  }

  private async stopConnection(): Promise<void> {
    const connection = this.connection;
    this.connection = null;
    if (!connection) {
      return;
    }

    try {
      connection.off('GroupMembershipChanged');
      await connection.stop();
    } catch {
      // Ignore teardown errors.
    }
  }

  private async ensureAccessToken(): Promise<string> {
    return (await this.session.ensureFreshAccessToken()) ?? '';
  }
}
