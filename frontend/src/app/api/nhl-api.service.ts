import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable } from 'rxjs';
import { OptimizationRequest, OptimizationResponse, Pos, StageBDemoPayload } from './models';

@Injectable({ providedIn: 'root' })
export class NhlApiService {
  constructor(private readonly http: HttpClient) {}

  getStageBDemo(baseUrl: string, pos: Pos): Observable<StageBDemoPayload> {
    return this.http.get<StageBDemoPayload>(`${baseUrl}/demo/goal1-stageb`, {
      params: { pos },
    });
  }

  optimize(baseUrl: string, pos: Pos, body: OptimizationRequest): Observable<OptimizationResponse> {
    const path = pos === 'fwd' ? 'forward-line' : 'defense-pair';
    return this.http.post<OptimizationResponse>(`${baseUrl}/optimize/${path}`, body);
  }

  validate(baseUrl: string, pos: Pos, playerIds: number[]): Observable<any> {
    const positionType = pos === 'fwd' ? 'forward' : 'defense';
    return this.http.post(`${baseUrl}/optimize/validate`, playerIds, {
      params: { position_type: positionType },
    });
  }

  getHealth(baseUrl: string): Observable<'ok'> {
    return this.http.get(`${baseUrl}/health`).pipe(map(() => 'ok' as const));
  }
}

