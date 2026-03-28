import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap, catchError, of } from 'rxjs';
import { env } from '../../env';

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private _user = signal<AuthUser | null>(null);
  readonly currentUser = this._user.asReadonly();
  readonly isLoggedIn = () => this._user() !== null;

  private get token(): string | null {
    return localStorage.getItem('auth_token');
  }

  checkSession() {
    if (!this.token) {
      this._user.set(null);
      return of(null);
    }
    return this.http.get<AuthUser>(`${env.apiUrl}/api/auth/me`).pipe(
      tap((user) => this._user.set(user)),
      catchError(() => {
        this._user.set(null);
        localStorage.removeItem('auth_token');
        return of(null);
      }),
    );
  }

  signup(email: string, password: string, name: string) {
    return this.http
      .post<{ token: string; user: AuthUser }>(`${env.apiUrl}/api/auth/sign-up`, { email, password, name })
      .pipe(
        tap(({ token, user }) => {
          localStorage.setItem('auth_token', token);
          this._user.set(user);
        }),
      );
  }

  login(email: string, password: string) {
    return this.http
      .post<{ token: string; user: AuthUser }>(`${env.apiUrl}/api/auth/sign-in`, { email, password })
      .pipe(
        tap(({ token, user }) => {
          localStorage.setItem('auth_token', token);
          this._user.set(user);
        }),
      );
  }

  logout() {
    localStorage.removeItem('auth_token');
    this._user.set(null);
    return of(null);
  }
}
