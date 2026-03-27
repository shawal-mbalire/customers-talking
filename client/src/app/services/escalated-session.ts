import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, timer, switchMap, shareReplay } from 'rxjs';
import { environment } from '../../environments/environment';

export interface EscalatedSession {
  sessionId: string;
  phoneNumber: string;
  lastIntent: string;
  timestamp: string;
  reason: string;
}

@Injectable({
  providedIn: 'root',
})
export class EscalatedSessionService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/api/sessions/escalated`;

  /** Polls the backend every 10 seconds. */
  sessions$: Observable<EscalatedSession[]> = timer(0, 10_000).pipe(
    switchMap(() => this.http.get<EscalatedSession[]>(this.baseUrl)),
    shareReplay(1),
  );

  resolve(sessionId: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/${sessionId}`);
  }
}
