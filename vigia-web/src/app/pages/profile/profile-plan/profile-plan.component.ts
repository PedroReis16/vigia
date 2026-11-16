import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { CardModule } from '@openng/optimus-ui/card';
import { UserPlan } from '@core/entities';
import { buildPlanView } from '@core/helpers';
import { GetUserPlanService } from '@core/usecases';

@Component({
  selector: 'app-profile-plan',
  standalone: true,
  imports: [TranslateModule, CardModule],
  templateUrl: './profile-plan.component.html',
  styleUrl: './profile-plan.component.css',
})
export class ProfilePlanComponent implements OnInit {
  private readonly getUserPlan = inject(GetUserPlanService);
  private readonly translate = inject(TranslateService);
  private readonly plan = signal<UserPlan | null>(null);
  readonly previewPackageId = signal<string | null>(null);
  private readonly language = toSignal(this.translate.onLangChange, {
    initialValue: { lang: this.translate.currentLang || 'pt-BR', translations: {} },
  });

  readonly active = computed(() => {
    const current = this.plan();
    if (!current) {
      return null;
    }

    return buildPlanView(current, current.currentPackageId, this.locale());
  });

  readonly draft = computed(() => {
    const current = this.plan();
    const previewId = this.previewPackageId();
    if (!current || !previewId || previewId === current.currentPackageId) {
      return null;
    }

    return buildPlanView(current, previewId, this.locale());
  });

  ngOnInit(): void {
    void this.getUserPlan.execute().then((plan) => this.plan.set(plan));
  }

  onPreviewPackage(id: string): void {
    const current = this.plan();
    if (!current || id === current.currentPackageId || id === this.previewPackageId()) {
      this.previewPackageId.set(null);
      return;
    }

    this.previewPackageId.set(id);
  }

  private locale(): string {
    return this.language().lang || 'pt-BR';
  }
}
