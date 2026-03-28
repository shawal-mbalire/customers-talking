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

  checkSession() {
    const stored = localStorage.getItem('auth_user');
    if (stored) {
      try { this._user.set(JSON.parse(stored)); } catch { /* ignore */ }
    }
    return of(this._user());
  }

  signup(email: string, _password: string, name: string) {
    // Stubbed — skip API call until auth backend is finalised
    const user: AuthUser = { id: crypto.randomUUID(), email, name };
    localStorage.setItem('auth_user', JSON.stringify(user));
    this._user.set(user);
    return of({ user });
  }

  login(email: string, _password: string) {
    // Stubbed — skip API call until auth backend is finalised
    const user: AuthUser = { id: crypto.randomUUID(), email };
    localStorage.setItem('auth_user', JSON.stringify(user));
    this._user.set(user);
    return of({ user });
  }

  logout() {
    localStorage.removeItem('auth_user');
    this._user.set(null);
    return of(null);
  }
}
