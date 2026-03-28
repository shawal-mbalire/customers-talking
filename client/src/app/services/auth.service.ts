import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap, catchError, of } from 'rxjs';
import { env } from '../../env';

interface AuthUser {
  id: string;
  username: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _user = signal<AuthUser | null>(null);
  readonly currentUser = this._user.asReadonly();
  readonly isLoggedIn = () => this._user() !== null;

  constructor(private http: HttpClient) {}

  /** Call once at app startup to restore session */
  checkSession() {
    return this.http
      .get<AuthUser>(`${env.apiUrl}/api/auth/me`, { withCredentials: true })
      .pipe(
        tap((user) => this._user.set(user)),
        catchError(() => {
          this._user.set(null);
          return of(null);
        }),
      );
  }

  login(username: string, password: string) {
    return this.http
      .post<AuthUser>(`${env.apiUrl}/api/auth/login`, { username, password }, { withCredentials: true })
      .pipe(tap((user) => this._user.set(user)));
  }

  logout() {
    return this.http
      .post(`${env.apiUrl}/api/auth/logout`, {}, { withCredentials: true })
      .pipe(tap(() => this._user.set(null)));
  }
}
