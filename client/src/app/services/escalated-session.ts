import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, timer, switchMap, shareReplay } from 'rxjs';
import { env } from '../../env';
import { SessionMessage } from './sessions.service';

export interface EscalatedSession {
  sessionId: string;
  phoneNumber: string;
  channel: string;
  lastIntent: string;
  reason: string;
  status: string;
  messages: SessionMessage[];
  awaitingSatisfaction: boolean;
  updatedAt: string;
  createdAt: string;
  /* legacy field kept for backward compat */
  timestamp?: string;
}

@Injectable({ providedIn: 'root' })
export class EscalatedSessionService {
  private http = inject(HttpClient);
  private baseUrl = `${env.apiUrl}/api/sessions/escalated`;

  sessions$: Observable<EscalatedSession[]> = timer(0, 10_000).pipe(
    switchMap(() => this.http.get<EscalatedSession[]>(this.baseUrl)),
    shareReplay(1),
  );

  resolve(sessionId: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/${sessionId}`);
  }
}
