import { Injectable } from '@angular/core';

const PENDING_INVITE_KEY = 'vigia.pendingInviteToken';

@Injectable({
  providedIn: 'root',
})
export class PendingInviteService {
  setToken(token: string): void {
    if (typeof sessionStorage === 'undefined') {
      return;
    }
    sessionStorage.setItem(PENDING_INVITE_KEY, token);
  }

  getToken(): string | null {
    if (typeof sessionStorage === 'undefined') {
      return null;
    }
    return sessionStorage.getItem(PENDING_INVITE_KEY);
  }

  clear(): void {
    if (typeof sessionStorage === 'undefined') {
      return;
    }
    sessionStorage.removeItem(PENDING_INVITE_KEY);
  }

  getPostAuthPath(): string {
    const token = this.getToken();
    return token ? `/invite/${token}` : '/devices';
  }
}
