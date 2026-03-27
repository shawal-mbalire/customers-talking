import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'handoff-monitor',
    pathMatch: 'full',
  },
  {
    path: 'handoff-monitor',
    loadComponent: () =>
      import('./pages/handoff-monitor/handoff-monitor').then(
        (m) => m.HandoffMonitorComponent,
      ),
  },
];
