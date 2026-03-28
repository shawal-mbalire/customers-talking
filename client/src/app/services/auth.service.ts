import { Injectable, signal } from '@angular/core';
import { from, tap, of, catchError, timeout } from 'rxjs';
import { authClient } from '../auth-client';

export interface AuthUser {
  id: string;
  email: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _user = signal<AuthUser | null>(null);
  readonly currentUser = this._user.asReadonly();
  readonly isLoggedIn = () => this._user() !== null;

  checkSession() {
    return from(authClient.getSession()).pipe(
      tap((session) => {
        const user = session?.data?.user;
        this._user.set(user ? { id: user.id, email: user.email } : null);
      }),
      catchError(() => {
        this._user.set(null);
        return of(null);
      }),
    );
  }

  signup(email: string, password: string, name: string) {
    return from(authClient.signUp.email({ email, password, name })).pipe(
      timeout(15_000),
      tap((result: any) => {
        if (result.error) throw result.error;
        const user = result.data?.user;
        this._user.set(user ? { id: user.id, email: user.email } : null);
      }),
      catchError((e) => { throw e; }),
    );
  }

  login(email: string, password: string) {
    return from(authClient.signIn.email({ email, password })).pipe(
      timeout(15_000),
      tap((result: any) => {
        if (result.error) throw result.error;
        const user = result.data?.user;
        this._user.set(user ? { id: user.id, email: user.email } : null);
      }),
      catchError((e) => { throw e; }),
    );
  }

  logout() {
    return from(authClient.signOut()).pipe(
      tap(() => this._user.set(null)),
    );
  }
}
