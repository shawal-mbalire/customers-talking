import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, timer, switchMap, shareReplay } from 'rxjs';
import { environment } from '../../environments/environment';

export interface UnifiedSession {
  sessionId: string;
  phoneNumber: string;
  channel: string;
  status: string;
  lastIntent: string;
  lastMessage: string;
  agentReply: string;
  reason: string;
  createdAt: string;
  updatedAt: string;
}

@Injectable({
  providedIn: 'root',
})
export class SessionsService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/api/sessions`;

  getSessions(status?: string, channel?: string): Observable<UnifiedSession[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (channel) params = params.set('channel', channel);
    return this.http.get<UnifiedSession[]>(this.baseUrl, { params });
  }

  resolve(sessionId: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/escalated/${sessionId}`);
  }
}
