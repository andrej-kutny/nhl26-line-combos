import { CommonModule } from '@angular/common';
import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { map } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { NhlApiService } from '../api/nhl-api.service';
import { LineSolution, OptimizationTarget, Pos } from '../api/models';

type Mode = 'demo' | 'live';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  protected readonly apiBaseUrl = signal('http://127.0.0.1:8000');
  protected readonly mode = signal<Mode>('demo');
  protected readonly pos = signal<Pos>('fwd');

  protected readonly minOvr = signal(80);
  protected readonly requireCenter = signal(false);
  protected readonly target = signal<OptimizationTarget>('ovr');
  protected readonly numSolutions = signal(5);

  protected readonly loading = signal(false);
  protected readonly status = signal<string>('');
  protected readonly solutions = signal<LineSolution[]>([]);

  protected readonly selectedSolution = signal<LineSolution | null>(null);
  protected readonly validateResult = signal<any>(null);

  protected readonly title = computed(() => {
    const posLabel = this.pos() === 'fwd' ? 'Forward line (3)' : 'Defense pair (2)';
    const modeLabel = this.mode() === 'demo' ? 'Demo' : 'Live';
    return `${modeLabel} • ${posLabel}`;
  });

  constructor(private readonly api: NhlApiService) {}

  protected run(): void {
    this.loading.set(true);
    this.status.set('');
    this.solutions.set([]);
    this.selectedSolution.set(null);
    this.validateResult.set(null);

    const baseUrl = this.apiBaseUrl().replace(/\/+$/, '');
    const pos = this.pos();

    const request$ = this.mode() === 'demo'
      ? this.api.getStageBDemo(baseUrl, pos).pipe(map((p) => ({ solutions: p.solutions })))
      : this.api.optimize(baseUrl, pos, {
            constraints: {
              min_ovr: this.minOvr(),
              require_center: this.requireCenter(),
            },
            optimization_target: this.target(),
            num_solutions: this.numSolutions(),
          }).pipe(map((r) => ({ solutions: r.solutions })));

    request$
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (data) => {
          const solutions = data.solutions ?? [];
          this.solutions.set(solutions);
          this.status.set(`Loaded ${solutions.length} solution(s).`);
        },
        error: (err: unknown) => {
          const anyErr = err as any;
          const msg = anyErr?.error?.detail ?? anyErr?.message ?? String(anyErr);
          this.status.set(`Error: ${msg}`);
        },
      });
  }

  protected select(sol: LineSolution): void {
    this.selectedSolution.set(sol);
    this.validateResult.set(null);
  }

  protected validateSelected(): void {
    const sol = this.selectedSolution();
    if (!sol) return;
    const baseUrl = this.apiBaseUrl().replace(/\/+$/, '');
    const ids = sol.players.map((p) => p.id);

    this.loading.set(true);
    this.api
      .validate(baseUrl, this.pos(), ids)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (data) => this.validateResult.set(data),
        error: (err: unknown) => {
          const anyErr = err as any;
          const msg = anyErr?.error?.detail ?? anyErr?.message ?? String(anyErr);
          this.status.set(`Validate error: ${msg}`);
        },
      });
  }
}
