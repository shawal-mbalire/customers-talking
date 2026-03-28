import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/landing/landing').then((m) => m.LandingComponent) },
  { path: 'login', redirectTo: '/sessions', pathMatch: 'full' },
  { path: 'sessions', loadComponent: () => import('./pages/sessions/sessions').then((m) => m.SessionsComponent) },
  { path: 'solutions', loadComponent: () => import('./pages/solutions/solutions').then((m) => m.SolutionsComponent) },
  { path: 'escalations', loadComponent: () => import('./pages/escalations/escalations').then((m) => m.EscalationsComponent) },
];
