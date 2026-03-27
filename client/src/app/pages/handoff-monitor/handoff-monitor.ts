import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe } from '@angular/common';
import { EscalatedSessionService, EscalatedSession } from '../../services/escalated-session';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmTableImports } from '@spartan-ng/helm/table';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmSkeletonImports } from '@spartan-ng/helm/skeleton';

@Component({
  selector: 'app-handoff-monitor',
  imports: [
    AsyncPipe,
    DatePipe,
    ...HlmCardImports,
    ...HlmTableImports,
    ...HlmBadgeImports,
    HlmButton,
    ...HlmSkeletonImports,
  ],
  templateUrl: './handoff-monitor.html',
  styleUrl: './handoff-monitor.scss',
})
export class HandoffMonitorComponent {
  private service = inject(EscalatedSessionService);

  sessions$ = this.service.sessions$;
  resolving: Record<string, boolean> = {};

  resolve(session: EscalatedSession): void {
    this.resolving[session.sessionId] = true;
    this.service.resolve(session.sessionId).subscribe({
      complete: () => delete this.resolving[session.sessionId],
      error: () => delete this.resolving[session.sessionId],
    });
  }
}
