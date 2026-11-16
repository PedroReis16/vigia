import { Component, inject, OnInit, signal } from '@angular/core';
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

  readonly failed = signal(false);
  private accepting = false;

  ngOnInit(): void {
    void this.accept();
  }

  retry(): void {
    void this.accept();
  }

  async accept(): Promise<void> {
    if (this.accepting) {
      return;
    }

    const token = this.route.snapshot.paramMap.get('token');
    if (!token) {
      await this.router.navigateByUrl('/devices');
      return;
    }

    this.accepting = true;
    this.failed.set(false);

    try {
      await this.acceptInvite.execute(token);
      this.pendingInvite.clear();
      this.messageService.addMessage({
        message: this.translate.instant('INVITE.SUCCESS'),
        type: 'success',
      });
      await this.router.navigateByUrl('/devices');
    } catch {
      this.pendingInvite.setToken(token);
      this.failed.set(true);
      this.messageService.addMessage({
        message: this.translate.instant('INVITE.ERROR'),
        type: 'error',
      });
    } finally {
      this.accepting = false;
    }
  }
}
