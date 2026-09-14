import { HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { DevicesService } from '@core/services';
import { firstValueFrom } from 'rxjs';
import { DevicesUseCaseError } from '../devices-use-case.error';

@Injectable({
  providedIn: 'root',
})
export class AcceptShareInviteService {
  private readonly devicesService = inject(DevicesService);

  async execute(token: string): Promise<void> {
    try {
      await firstValueFrom(this.devicesService.acceptShareInvite(token));
    } catch (error: unknown) {
      throw this.toDevicesError(error);
    }
  }

  private toDevicesError(error: unknown): DevicesUseCaseError {
    if (error instanceof HttpErrorResponse) {
      return new DevicesUseCaseError('INVITE.ERROR', error.status);
    }
    return new DevicesUseCaseError('INVITE.ERROR');
  }
}
