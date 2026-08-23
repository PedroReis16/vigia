import {
  HttpBackend,
  HttpClient,
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthTokensDto } from '@core/entities/DTOs/auth.dto';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { environment } from '@environments/environment';
import { catchError, Observable, switchMap, throwError } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly session = inject(AuthSessionService);
  private readonly refreshHttp = new HttpClient(inject(HttpBackend));

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const skipAuth = req.headers.get('Skip-Auth') === 'true';
    let request = req;

    if (skipAuth) {
      request = req.clone({
        headers: req.headers.delete('Skip-Auth'),
      });
    } else {
      const accessToken = this.session.getAccessToken();
      if (accessToken) {
        request = req.clone({
          setHeaders: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      }
    }

    return next.handle(request).pipe(
      catchError((error: unknown) => {
        if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
          return throwError(() => error);
        }

        if (skipAuth || this.isPublicAuthPath(request.url) || req.headers.has('X-Auth-Retry')) {
          return throwError(() => error);
        }

        const refreshToken = this.session.getRefreshToken();
        if (!refreshToken) {
          this.session.clearSession();
          return throwError(() => error);
        }

        const base = environment.apiUrl.replace(/\/$/, '');
        return this.refreshHttp
          .post<AuthTokensDto>(`${base}/auth/refresh`, { refreshToken })
          .pipe(
            switchMap((tokens) => {
              this.session.setSession(tokens);
              const retryReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${tokens.accessToken}`,
                  'X-Auth-Retry': 'true',
                },
              });
              return next.handle(retryReq);
            }),
            catchError((refreshError: unknown) => {
              this.session.clearSession();
              return throwError(() => refreshError);
            }),
          );
      }),
    );
  }

  private isPublicAuthPath(url: string): boolean {
    return (
      url.includes('/auth/login') ||
      url.includes('/auth/register') ||
      url.includes('/auth/refresh')
    );
  }
}
