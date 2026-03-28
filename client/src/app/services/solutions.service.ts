import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { env } from '../../env';

export interface Solution {
  id: string;
  question: string;
  answer: string;
  intentName: string;
  triggerPhrases: string[];
  channels: string[];
  active: boolean;
  createdAt: string;
}

export interface SolutionPayload {
  question: string;
  answer: string;
  intentName?: string;
  triggerPhrases?: string[];
  channels?: string[];
  active?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class SolutionsService {
  private http = inject(HttpClient);
  private baseUrl = `${env.apiUrl}/api/solutions`;

  getAll(): Observable<Solution[]> {
    return this.http.get<Solution[]>(this.baseUrl);
  }

  create(payload: SolutionPayload): Observable<Solution> {
    return this.http.post<Solution>(this.baseUrl, payload);
  }

  update(id: string, payload: SolutionPayload): Observable<Solution> {
    return this.http.put<Solution>(`${this.baseUrl}/${id}`, payload);
  }

  delete(id: string): Observable<unknown> {
    return this.http.delete(`${this.baseUrl}/${id}`);
  }
}
