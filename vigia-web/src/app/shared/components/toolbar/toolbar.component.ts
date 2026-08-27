import { Component, computed, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { Avatar } from '@openng/optimus-ui/avatar';
import { Popover } from '@openng/optimus-ui/popover';
import { captureToolbarHeight, captureToolbarLogoBounds } from '@core/helpers';
import { AuthExitTransitionService, MessageService } from '@core/services';
import { LogoutService } from '@core/usecases';

@Component({
  selector: 'app-toolbar',
  imports: [TranslateModule, RouterLink, Avatar, Popover],
  standalone: true,
  templateUrl: './toolbar.component.html',
  styleUrl: './toolbar.component.css',
})
export class ToolbarComponent {
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly logout = inject(LogoutService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);

  readonly userMenu = viewChild.required<Popover>('userMenu');

  readonly showToolbarLogo = computed(
    () =>
      this.authExitTransition.settled() ||
      this.authExitTransition.toolbarLogoRevealed(),
  );
  readonly toolbarLogoSrc = computed(() =>
    this.authExitTransition.settled()
      ? 'images/vigia-logo.png'
      : 'images/vigia-logo-dark.png',
  );
  readonly logoutMorphActive = computed(
    () =>
      this.authExitTransition.kind() === 'logout' &&
      !this.authExitTransition.settled(),
  );

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
    const menuWidth = container.offsetWidth;
    container.style.left = `${targetRect.right - menuWidth}px`;
    const arrowLeft = menuWidth - targetRect.width / 2;
    container.style.setProperty('--p-popover-arrow-left', `${arrowLeft}px`);
  }

  async onLogout(): Promise<void> {
    this.userMenu().hide();

    const reducedMotion = this.prefersReducedMotion();

    if (!reducedMotion) {
      const logo = captureToolbarLogoBounds();
      const toolbarHeight = captureToolbarHeight();
      if (logo && toolbarHeight) {
        this.authExitTransition.armLogout(logo, toolbarHeight);
        await this.authExitTransition.waitForShellExit();
      }
    }

    await this.logout.execute();
    this.messageService.removeMessage();
    await this.router.navigate(['/login']);
  }

  private prefersReducedMotion(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }
}
