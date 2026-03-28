import { HttpInterceptorFn } from '@angular/common/http';
import { from, switchMap } from 'rxjs';
import { authClient } from '../auth-client';
import { env } from '../../env';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(env.apiUrl)) {
    return next(req);
  }
  return from(authClient.getSession()).pipe(
    switchMap((session) => {
      const token = (session?.data?.session as any)?.access_token ?? (session?.data?.session as any)?.token;
      if (!token) return next(req);
      return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
    }),
  );
};
