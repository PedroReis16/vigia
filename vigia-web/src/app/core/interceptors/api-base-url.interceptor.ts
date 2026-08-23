import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '@environments/environment';

@Injectable()
export class ApiBaseUrlInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    if (!this.shouldPrefix(req.url)) {
      return next.handle(req);
    }

    const base = environment.apiUrl.replace(/\/$/, '');
    const path = req.url.startsWith('/') ? req.url : `/${req.url}`;
    const apiReq = req.clone({ url: `${base}${path}` });
    return next.handle(apiReq);
  }

  private shouldPrefix(url: string): boolean {
    if (!url || url.startsWith('http://') || url.startsWith('https://') || url.startsWith('//')) {
      return false;
    }

    // Absolute API-style paths only (e.g. /auth/login). Skip relative assets like ./i18n/...
    return url.startsWith('/');
  }
}
