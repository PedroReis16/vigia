import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { AcceptShareInviteService } from '@core/usecases';
import { MessageService, PendingInviteService } from '@core/services';

@Component({
  selector: 'app-accept-invite',
  standalone: true,
  imports: [TranslateModule],
  templateUrl: './accept-invite.component.html',
  styleUrl: './accept-invite.component.css',
})
export class AcceptInviteComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly acceptInvite = inject(AcceptShareInviteService);
  private readonly pendingInvite = inject(PendingInviteService);
  private readonly messageService = inject(MessageService);
  private readonly translate = inject(TranslateService);

  private started = false;

  ngOnInit(): void {
    void this.accept();
  }

  private async accept(): Promise<void> {
    if (this.started) {
      return;
    }
    this.started = true;

    const token = this.route.snapshot.paramMap.get('token');
    if (!token) {
      await this.router.navigateByUrl('/devices');
      return;
    }

    try {
      await this.acceptInvite.execute(token);
      this.pendingInvite.clear();
      this.messageService.addMessage({
        message: this.translate.instant('INVITE.SUCCESS'),
        type: 'success',
      });
    } catch {
      this.pendingInvite.clear();
      this.messageService.addMessage({
        message: this.translate.instant('INVITE.ERROR'),
        type: 'error',
      });
    }

    await this.router.navigateByUrl('/devices');
  }
}
