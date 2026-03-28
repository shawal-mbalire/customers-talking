import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/landing/landing').then((m) => m.LandingComponent) },
  { path: 'sessions', loadComponent: () => import('./pages/sessions/sessions').then((m) => m.SessionsComponent) },
  { path: 'solutions', loadComponent: () => import('./pages/solutions/solutions').then((m) => m.SolutionsComponent) },
  { path: 'handoff-monitor', loadComponent: () => import('./pages/handoff-monitor/handoff-monitor').then((m) => m.HandoffMonitorComponent) },
];
