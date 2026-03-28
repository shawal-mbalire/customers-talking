import { Injectable, signal } from '@angular/core';

function resolveInitialDark(): boolean {
  const saved = localStorage.getItem('theme');
  if (saved === 'dark') return true;
  if (saved === 'light') return false;
  // No saved preference — follow OS
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private _dark = signal(resolveInitialDark());
  readonly isDark = this._dark.asReadonly();

  init(): void {
    document.documentElement.classList.toggle('dark', this._dark());

    // Keep in sync when OS preference changes (only if user hasn't overridden)
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        this._dark.set(e.matches);
        document.documentElement.classList.toggle('dark', e.matches);
      }
    });
  }

  toggle(): void {
    const dark = !this._dark();
    this._dark.set(dark);
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }
}
