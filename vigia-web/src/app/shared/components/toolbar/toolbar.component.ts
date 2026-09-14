import { Component, computed, inject, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { Avatar } from '@openng/optimus-ui/avatar';
import { Popover } from '@openng/optimus-ui/popover';
import { FallNotification } from '@core/entities';
import { captureToolbarHeight, captureToolbarLogoBounds } from '@core/helpers';
import {
  AuthExitTransitionService,
  MessageService,
  NotificationStoreService,
} from '@core/services';
import { LogoutService, NavigateToFallAlertService, SyncPushNotificationsService } from '@core/usecases';
import moment from 'moment';

@Component({
  selector: 'app-toolbar',
  standalone: true,
  imports: [RouterLink, TranslateModule, Avatar, Popover],
  templateUrl: './toolbar.component.html',
  styleUrl: './toolbar.component.css',
})
export class ToolbarComponent {
  private readonly authExitTransition = inject(AuthExitTransitionService);
  private readonly logout = inject(LogoutService);
  private readonly router = inject(Router);
  private readonly messageService = inject(MessageService);
  private readonly notificationStore = inject(NotificationStoreService);
  private readonly navigateToFallAlert = inject(NavigateToFallAlertService);
  private readonly syncPushNotifications = inject(SyncPushNotificationsService);

  readonly userMenu = viewChild.required<Popover>('userMenu');
  readonly notificationsMenu = viewChild.required<Popover>('notificationsMenu');

  readonly notifications = this.notificationStore.notifications;
  readonly unreadCount = this.notificationStore.unreadCount;
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
    this.notificationsMenu().hide();
    this.userMenu().toggle(event);
  }

  toggleNotifications(event: Event): void {
    this.userMenu().hide();
    void this.syncPushNotifications.execute().finally(() => {
      this.notificationsMenu().toggle(event);
    });
  }

  get notificationsBlocked(): boolean {
    return typeof Notification !== 'undefined' && Notification.permission === 'denied';
  }

  get notificationsNeedPermission(): boolean {
    return typeof Notification !== 'undefined' && Notification.permission === 'default';
  }

  /** Pin the popover's right edge to the trigger (flush right). */
  alignPopoverToRight(popover: Popover): void {
    const container = popover.container;
    const target = popover.target as HTMLElement | undefined;
    if (!container || !target) {
      return;
    }

    const targetRect = target.getBoundingClientRect();
    const left = Math.max(8, targetRect.right - container.offsetWidth + window.scrollX);
    container.style.left = `${left}px`;

    const arrowLeft = targetRect.left + targetRect.width / 2 - (left - window.scrollX);
    container.style.setProperty('--p-popover-arrow-left', `${arrowLeft}px`);
  }

  alignUserMenuToRight(): void {
    this.alignPopoverToRight(this.userMenu());
  }

  alignNotificationsMenuToRight(): void {
    this.alignPopoverToRight(this.notificationsMenu());
  }

  formatRelativeTime(receivedAt: string): string {
    return moment(receivedAt).fromNow();
  }

  displayDeviceName(notification: FallNotification): string {
    return notification.nickname || notification.deviceName || notification.deviceId;
  }

  async onNotificationClick(notification: FallNotification): Promise<void> {
    this.notificationStore.markRead(notification.id);
    this.notificationsMenu().hide();
    await this.navigateToFallAlert.execute({
      type: 'fall',
      deviceId: notification.deviceId,
    });
  }

  onMarkAllRead(): void {
    this.notificationStore.markAllRead();
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
