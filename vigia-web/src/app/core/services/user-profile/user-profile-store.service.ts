import { Injectable, signal } from '@angular/core';
import { UserProfile } from '@core/entities/classes/user-profile';

@Injectable({
  providedIn: 'root',
})
export class UserProfileStoreService {
  private readonly profileState = signal<UserProfile | null>(null);

  readonly profile = this.profileState.asReadonly();

  set(profile: UserProfile | null): void {
    this.profileState.set(profile);
  }
}
