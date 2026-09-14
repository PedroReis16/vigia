import { NgTemplateOutlet } from '@angular/common';
import { Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-device-detail-action-row',
  standalone: true,
  imports: [NgTemplateOutlet, TranslateModule, RouterLink],
  templateUrl: './device-detail-action-row.component.html',
  styleUrl: './device-detail-action-row.component.css',
})
export class DeviceDetailActionRowComponent {
  readonly icon = input.required<string>();
  readonly title = input.required<string>();
  readonly description = input<string | null>(null);
  readonly meta = input<string | null>(null);
  readonly disabled = input(false);
  readonly routerLink = input<string | readonly string[] | null>(null);
  readonly testId = input<string | null>(null);
  readonly embedded = input(false);

  readonly action = output<void>();

  onAction(event: Event): void {
    if (this.disabled()) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    this.action.emit();
  }
}
