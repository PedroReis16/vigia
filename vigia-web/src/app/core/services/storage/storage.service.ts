import { Injectable } from '@angular/core';
import { Storage } from '@core/interfaces';

@Injectable({
  providedIn: 'root',
})
export class StorageService implements Storage {
  getItem(key: string): string | null {
    return localStorage.getItem(key);
  }

  removeItem(key: string): void {
    localStorage.removeItem(key);
  }

  setItem(key: string, data: string): void {
    localStorage.setItem(key, data);
  }
}
