import { Component, inject, OnInit, OnDestroy, signal } from '@angular/core';
import { AsyncPipe, UpperCasePipe, DatePipe } from '@angular/common';
import { Observable, Subscription, timer, switchMap, shareReplay } from 'rxjs';
import { SessionsService, UnifiedSession } from '../../services/sessions.service';
import { BadgeVariants } from '@spartan-ng/helm/badge';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmTableImports } from '@spartan-ng/helm/table';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmSkeletonImports } from '@spartan-ng/helm/skeleton';
import { HlmSeparatorImports } from '@spartan-ng/helm/separator';

type BV = BadgeVariants['variant'];

@Component({
  selector: 'app-sessions',
  imports: [
    AsyncPipe,
    UpperCasePipe,
    DatePipe,
    ...HlmCardImports,
    ...HlmTableImports,
    ...HlmBadgeImports,
    HlmButton,
    ...HlmSkeletonImports,
    ...HlmSeparatorImports,
  ],
  templateUrl: './sessions.html',
})
export class SessionsComponent implements OnInit, OnDestroy {
  private service = inject(SessionsService);

  sessions$!: Observable<UnifiedSession[]>;
  channelFilter = '';
  statusFilter = '';
  resolving: Record<string, boolean> = {};
  expanded = signal<string | null>(null);

  private sub?: Subscription;

  ngOnInit(): void { this._refresh(); }
  ngOnDestroy(): void { this.sub?.unsubscribe(); }

  setChannelFilter(v: string): void { this.channelFilter = v; this._refresh(); }
  setStatusFilter(v: string): void { this.statusFilter = v; this._refresh(); }

  toggleContext(sessionId: string): void {
    this.expanded.update((cur) => (cur === sessionId ? null : sessionId));
  }

  resolve(s: UnifiedSession): void {
    this.resolving[s.sessionId] = true;
    this.service.resolve(s.sessionId).subscribe({
      complete: () => { delete this.resolving[s.sessionId]; this._refresh(); },
      error: () => delete this.resolving[s.sessionId],
    });
  }

  channelVariant(ch: string): BV {
    return ({ ussd: 'secondary', sms: 'default', voice: 'outline' } as Record<string, BV>)[ch] ?? 'outline';
  }

  statusVariant(st: string): BV {
    return ({ active: 'secondary', escalated: 'destructive', resolved: 'outline' } as Record<string, BV>)[st] ?? 'outline';
  }

  skeletonRows = [1, 2, 3, 4, 5];

  private _refresh(): void {
    this.sessions$ = timer(0, 10_000).pipe(
      switchMap(() => this.service.getSessions(this.statusFilter || undefined, this.channelFilter || undefined)),
      shareReplay(1),
    );
  }
}
