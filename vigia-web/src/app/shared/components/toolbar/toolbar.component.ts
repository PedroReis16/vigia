import { Component, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { Avatar } from '@openng/optimus-ui/avatar';
import { Popover } from '@openng/optimus-ui/popover';
import { MessageService } from '@core/services';
import { LogoutService } from '@core/usecases';

@Component({
  selector: 'app-toolbar',
  standalone: true,
  imports: [RouterLink, TranslateModule, Avatar, Popover],
  templateUrl: './toolbar.component.html',
  styleUrl: './toolbar.component.css',
})
export class ToolbarComponent {
  private readonly logout = inject(LogoutService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);

  readonly userMenu = viewChild.required<Popover>('userMenu');

  /** Reserved for when the API exposes a profile picture URL. */
  readonly userPictureUrl: string | null = null;

  toggleUserMenu(event: Event): void {
    this.userMenu().toggle(event);
  }

  /** Pin the popover's right edge to the avatar (flush right). */
  alignUserMenuToRight(): void {
    const menu = this.userMenu();
    const container = menu.container;
    const target = menu.target as HTMLElement | undefined;
    if (!container || !target) {
      return;
    }

    const targetRect = target.getBoundingClientRect();
    const left = Math.max(8, targetRect.right - container.offsetWidth + window.scrollX);
    container.style.left = `${left}px`;

    const arrowLeft = targetRect.left + targetRect.width / 2 - (left - window.scrollX);
    container.style.setProperty('--p-popover-arrow-left', `${arrowLeft}px`);
  }

  async onLogout(): Promise<void> {
    this.userMenu().hide();
    await this.logout.execute();
    this.messageService.removeMessage();
    await this.router.navigate(['/login']);
  }
}
