import { inject, Injectable, OnDestroy } from '@angular/core';
import {
  GroupMembershipChangedDto,
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

  readonly membershipChanged$ = this.membershipChangedSubject.asObservable();

  ngOnDestroy(): void {
    void this.disconnect();
    this.membershipChangedSubject.complete();
  }

  get isConnected(): boolean {
    return this.connection?.state === HubConnectionState.Connected;
  }

  async connect(): Promise<void> {
    const current = this.connection;
    if (
      current &&
      (current.state === HubConnectionState.Connected ||
        current.state === HubConnectionState.Connecting ||
        current.state === HubConnectionState.Reconnecting)
    ) {
      return;
    }

    await this.disconnect();

    const token = await this.ensureAccessToken();
    if (!token) {
      return;
    }

    const hubUrl = `${environment.apiUrl.replace(/\/$/, '')}/hubs/device-groups`;
    const connection = new HubConnectionBuilder()
      .withUrl(hubUrl, {
        accessTokenFactory: () => this.ensureAccessToken(),
      })
      .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
      .build();

    connection.on('GroupMembershipChanged', (...args: unknown[]) => {
      const event = parseGroupMembershipChanged(args[0]);
      if (event) {
        this.membershipChangedSubject.next(event);
      }
    });

    this.connection = connection;
    await connection.start();
  }

  async disconnect(): Promise<void> {
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
