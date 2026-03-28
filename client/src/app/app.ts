import { Component, inject, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { HlmButton } from '@spartan-ng/helm/button';
import { ThemeService } from './services/theme.service';
import { AuthService } from './services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, HlmButton],
  templateUrl: './app.html',
})
export class App implements OnInit {
  theme = inject(ThemeService);
  auth = inject(AuthService);
  private router = inject(Router);

  constructor() {
    this.theme.init();
  }

  ngOnInit() {
    this.auth.checkSession().subscribe();
  }

  logout() {
    this.auth.logout().subscribe(() => this.router.navigateByUrl('/login'));
  }
}
