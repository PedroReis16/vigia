import { inject, Injectable } from '@angular/core';
import { DevicesService } from '@core/services';
import { tap } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class GetDevicesService {
  private readonly devicesService = inject(DevicesService);

  execute() {
    return this.devicesService.getDevices().pipe(
      tap((response) => {
        console.log(response);
      }),
    );
  }
}
