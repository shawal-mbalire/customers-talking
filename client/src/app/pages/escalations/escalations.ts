import { Component, inject, signal } from '@angular/core';
import { AsyncPipe, DatePipe, UpperCasePipe } from '@angular/common';
import { EscalatedSessionService, EscalatedSession } from '../../services/escalated-session';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmTableImports } from '@spartan-ng/helm/table';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmSkeletonImports } from '@spartan-ng/helm/skeleton';

@Component({
  selector: 'app-escalations',
  imports: [
    AsyncPipe,
    DatePipe,
    UpperCasePipe,
    ...HlmCardImports,
    ...HlmTableImports,
    ...HlmBadgeImports,
    HlmButton,
    ...HlmSkeletonImports,
  ],
  templateUrl: './escalations.html',
  styleUrl: './escalations.scss',
})
export class EscalationsComponent {
  private service = inject(EscalatedSessionService);

  sessions$ = this.service.sessions$;
  expanded = signal<string | null>(null);
  resolving: Record<string, boolean> = {};

  toggleContext(s: EscalatedSession): void {
    this.expanded.update((cur) => (cur === s.sessionId ? null : s.sessionId));
  }

  resolve(session: EscalatedSession): void {
    this.resolving[session.sessionId] = true;
    this.service.resolve(session.sessionId).subscribe({
      complete: () => delete this.resolving[session.sessionId],
      error: () => delete this.resolving[session.sessionId],
    });
  }
}
