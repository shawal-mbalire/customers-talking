import { Component, inject, OnInit } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SolutionsService, Solution } from '../../services/solutions.service';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmTableImports } from '@spartan-ng/helm/table';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmInputImports } from '@spartan-ng/helm/input';
import { HlmTextareaImports } from '@spartan-ng/helm/textarea';
import { HlmLabelImports } from '@spartan-ng/helm/label';
import { HlmSeparatorImports } from '@spartan-ng/helm/separator';
import { HlmCheckboxImports } from '@spartan-ng/helm/checkbox';

@Component({
  selector: 'app-solutions',
  imports: [
    ReactiveFormsModule,
    ...HlmCardImports,
    ...HlmTableImports,
    ...HlmBadgeImports,
    HlmButton,
    ...HlmInputImports,
    ...HlmTextareaImports,
    ...HlmLabelImports,
    ...HlmSeparatorImports,
    ...HlmCheckboxImports,
  ],
  templateUrl: './solutions.html',
})
export class SolutionsComponent implements OnInit {
  private service = inject(SolutionsService);
  private fb = inject(FormBuilder);

  solutions: Solution[] = [];
  loading = true;
  showAddForm = false;
  editingId: string | null = null;
  saving = false;

  form: FormGroup = this.fb.group({
    question: ['', Validators.required],
    answer: ['', Validators.required],
    intentName: [''],
    triggerPhrases: [''],
    active: [true],
  });

  ngOnInit(): void {
    this._load();
  }

  toggleAddForm(): void {
    this.showAddForm = !this.showAddForm;
    this.editingId = null;
    this.form.reset({ active: true });
  }

  startEdit(solution: Solution): void {
    this.editingId = solution.id;
    this.showAddForm = true;
    this.form.patchValue({
      question: solution.question,
      answer: solution.answer,
      intentName: solution.intentName,
      triggerPhrases: solution.triggerPhrases.join(', '),
      active: solution.active,
    });
  }

  cancelEdit(): void {
    this.showAddForm = false;
    this.editingId = null;
    this.form.reset({ active: true });
  }

  save(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.value;
    const payload = {
      question: raw.question,
      answer: raw.answer,
      intentName: raw.intentName || '',
      triggerPhrases: raw.triggerPhrases
        ? raw.triggerPhrases.split(',').map((p: string) => p.trim()).filter(Boolean)
        : [],
      channels: ['all'],
      active: raw.active ?? true,
    };

    const req$ = this.editingId
      ? this.service.update(this.editingId, payload)
      : this.service.create(payload);

    req$.subscribe({
      complete: () => {
        this.saving = false;
        this.cancelEdit();
        this._load();
      },
      error: () => (this.saving = false),
    });
  }

  deleteSolution(id: string): void {
    if (!confirm('Delete this solution?')) return;
    this.service.delete(id).subscribe({ complete: () => this._load() });
  }

  private _load(): void {
    this.loading = true;
    this.service.getAll().subscribe({
      next: (data) => {
        this.solutions = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
