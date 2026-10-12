import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface UserNotificationDto {
  id: string;
  episodeId: string;
  deviceId: string;
  type: string;
  title: string;
  body: string;
  createdAt: string;
  read: boolean;
  readAt?: string | null;
}

export interface NotificationListDto {
  items: UserNotificationDto[];
  unreadCount: number;
}

@Injectable({
  providedIn: 'root',
})
export class NotificationsHttpService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/notifications';

  list(skip?: number, take?: number): Observable<NotificationListDto> {
    const params: Record<string, string> = {};
    if (skip != null) {
      params['skip'] = String(skip);
    }
    if (take != null) {
      params['take'] = String(take);
    }
    return this.http.get<NotificationListDto>(this.basePath, { params });
  }

  markRead(notificationId: string): Observable<void> {
    return this.http.post<void>(`${this.basePath}/${notificationId}/read`, {});
  }

  markAllRead(): Observable<void> {
    return this.http.post<void>(`${this.basePath}/read-all`, {});
  }
}
