import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { UserProfileDto } from '@core/entities';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UserProfileHttpService {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/users';

  getProfile(): Observable<UserProfileDto> {
    return this.http.get<UserProfileDto>(`${this.basePath}/me`);
  }

  uploadPicture(file: File): Observable<UserProfileDto> {
    const body = new FormData();
    body.append('file', file);
    return this.http.put<UserProfileDto>(`${this.basePath}/me/picture`, body);
  }

  removePicture(): Observable<UserProfileDto> {
    return this.http.delete<UserProfileDto>(`${this.basePath}/me/picture`);
  }

  updateProfile(profile: {
    firstName: string;
    lastName: string;
    phone: string;
  }): Observable<UserProfileDto> {
    return this.http.put<UserProfileDto>(`${this.basePath}/me`, profile);
  }

  deleteAccount(): Observable<void> {
    return this.http.delete<void>(`${this.basePath}/me`);
  }
}
