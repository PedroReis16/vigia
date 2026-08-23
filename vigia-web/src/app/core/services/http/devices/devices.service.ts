import { HttpClient, HttpResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DeviceDto } from '@core/entities/DTOs/device.dto';
import { map, Observable } from 'rxjs';

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

  private normalizeListResponse(response: HttpResponse<DeviceDto[] | null>): DeviceDto[] {
    if (response.status === 204 || response.body == null) {
      return [];
    }

    return Array.isArray(response.body) ? response.body : [];
  }
}
