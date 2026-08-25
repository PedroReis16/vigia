import { HttpClient, HttpResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import {
  DeviceDto,
  DeviceShareInviteDto,
  DeviceUserDto,
  UpdateDeviceDto,
} from '@core/entities';
import { map, Observable } from 'rxjs';

export interface DeviceCommandRequest {
  command: string;
  commandValue?: string;
}

@Injectable({
  providedIn: 'root',
})
export class DevicesService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/devices';

  getDevices(): Observable<DeviceDto[]> {
    return this.http
      .get<DeviceDto[] | null>(`${this.basePath}/list`, { observe: 'response' })
      .pipe(map((response) => this.normalizeListResponse(response)));
  }

  getDevice(deviceId: string): Observable<DeviceDto | null> {
    return this.http
      .get<DeviceDto | null>(`${this.basePath}/${deviceId}`, { observe: 'response' })
      .pipe(map((response) => this.normalizeSingleResponse(response)));
  }

  updateDevice(deviceId: string, body: UpdateDeviceDto): Observable<void> {
    return this.http.put<void>(`${this.basePath}/${deviceId}`, body);
  }

  sendCommand(deviceId: string, command: string, commandValue = ''): Observable<void> {
    const body: DeviceCommandRequest = { command, commandValue };
    return this.http.patch<void>(`${this.basePath}/${deviceId}/command`, body);
  }

  getDeviceUsers(deviceId: string): Observable<DeviceUserDto[]> {
    return this.http.get<DeviceUserDto[]>(`${this.basePath}/${deviceId}/users`);
  }

  generateShareLink(deviceId: string): Observable<DeviceShareInviteDto> {
    return this.http.get<DeviceShareInviteDto>(`${this.basePath}/${deviceId}/share/generate`);
  }

  removeDeviceUser(deviceId: string, userId: string): Observable<void> {
    return this.http.delete<void>(`${this.basePath}/${deviceId}/users/${userId}`);
  }

  private normalizeListResponse(response: HttpResponse<DeviceDto[] | null>): DeviceDto[] {
    if (response.status === 204 || response.body == null) {
      return [];
    }

    return Array.isArray(response.body) ? response.body : [];
  }

  private normalizeSingleResponse(response: HttpResponse<DeviceDto | null>): DeviceDto | null {
    if (response.status === 204 || response.body == null) {
      return null;
    }

    return response.body;
  }
}
