import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmInput } from '@spartan-ng/helm/input';
import { HlmLabel } from '@spartan-ng/helm/label';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, ...HlmCardImports, HlmButton, HlmInput, HlmLabel],
  templateUrl: './login.html',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);

  mode = signal<'login' | 'signup'>('login');

  form = this.fb.nonNullable.group({
    name: [''],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });
  error = signal('');
  loading = signal(false);

  toggleMode() {
    this.mode.set(this.mode() === 'login' ? 'signup' : 'login');
    this.error.set('');
    this.form.reset();
  }

  submit() {
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set('');
    const { email, password, name } = this.form.getRawValue();

    const action$ = this.mode() === 'signup'
      ? this.auth.signup(email, password, name)
      : this.auth.login(email, password);

    action$.subscribe({
      next: () => this.router.navigateByUrl('/sessions'),
      error: (e) => {
        const isTimeout = e?.name === 'TimeoutError';
        this.error.set(
          isTimeout
            ? 'Request timed out — please check your connection and try again.'
            : (e?.error?.error ?? e?.message ?? (this.mode() === 'signup' ? 'Sign up failed' : 'Login failed'))
        );
        this.loading.set(false);
      },
    });
  }
}
