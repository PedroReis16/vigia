import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { AuthSessionService } from '@core/services/auth/auth-session.service';
import { catchError, from, Observable, switchMap, throwError } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly session = inject(AuthSessionService);

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

        if (skipAuth || req.headers.has('X-Auth-Retry')) {
          return throwError(() => error);
        }

        return from(this.session.forceRefreshAccessToken()).pipe(
          switchMap((accessToken) => {
            if (!accessToken) {
              this.session.clearSession();
              return throwError(() => error);
            }

            const retryReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${accessToken}`,
                'X-Auth-Retry': 'true',
              },
            });
            return next.handle(retryReq);
          }),
        );
      }),
    );
  }
}
