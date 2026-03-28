import { Injectable, signal } from '@angular/core';
import { from, switchMap, tap, of, catchError } from 'rxjs';
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
      tap((result: any) => {
        if (result.error) throw result.error;
        const user = result.data?.user;
        this._user.set(user ? { id: user.id, email: user.email } : null);
      }),
    );
  }

  login(email: string, password: string) {
    return from(authClient.signIn.email({ email, password })).pipe(
      tap((result: any) => {
        if (result.error) throw result.error;
        const user = result.data?.user;
        this._user.set(user ? { id: user.id, email: user.email } : null);
      }),
    );
  }

  logout() {
    return from(authClient.signOut()).pipe(
      tap(() => this._user.set(null)),
    );
  }
}
