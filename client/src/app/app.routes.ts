import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/landing/landing').then((m) => m.LandingComponent) },
  { path: 'login', loadComponent: () => import('./pages/login/login').then((m) => m.LoginComponent) },
  { path: 'sessions', loadComponent: () => import('./pages/sessions/sessions').then((m) => m.SessionsComponent), canActivate: [authGuard] },
  { path: 'solutions', loadComponent: () => import('./pages/solutions/solutions').then((m) => m.SolutionsComponent), canActivate: [authGuard] },
  { path: 'escalations', loadComponent: () => import('./pages/escalations/escalations').then((m) => m.EscalationsComponent), canActivate: [authGuard] },
];
