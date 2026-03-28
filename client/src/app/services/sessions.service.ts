import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { env } from '../../env';

export interface SessionMessage {
  role: 'user' | 'bot' | 'system';
  text: string;
  ts: string;
}

export interface UnifiedSession {
  sessionId: string;
  phoneNumber: string;
  channel: string;
  status: string;
  lastIntent: string;
  lastMessage: string;
  agentReply: string;
  reason: string;
  messages: SessionMessage[];
  awaitingSatisfaction: boolean;
  createdAt: string;
  updatedAt: string;
}

@Injectable({ providedIn: 'root' })
export class SessionsService {
  private http = inject(HttpClient);
  private baseUrl = `${env.apiUrl}/api/sessions`;

  getSessions(status?: string, channel?: string): Observable<UnifiedSession[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (channel) params = params.set('channel', channel);
    return this.http.get<UnifiedSession[]>(this.baseUrl, { params, withCredentials: true });
  }

  resolve(sessionId: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/escalated/${sessionId}`, { withCredentials: true });
  }
}
