import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class DevicesService {
  private readonly http = inject(HttpClient);

  getDevices(): Observable<unknown> {
    return this.http.get<unknown>('https://api.github.com/devices', {
      headers: { 'Skip-Auth': 'true' },
    });
  }
}
