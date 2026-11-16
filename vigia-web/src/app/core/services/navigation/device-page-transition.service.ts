import { DOCUMENT } from '@angular/common';
import { Injectable, inject } from '@angular/core';
import { NavigationCancel, NavigationError, Router, RoutesRecognized } from '@angular/router';
import {
  devicePageTransitionDirection,
  routeSnapshotPath,
  type RouteUrlNode,
} from '@core/helpers/device-page-transition.helper';

const PAGE_TRANSITION_NAME = 'device-page';

interface PageViewTransition {
  skipTransition: () => void;
  finished: Promise<unknown>;
}

@Injectable({ providedIn: 'root' })
export class DevicePageTransitionService {
  private readonly router = inject(Router);
  private readonly document = inject(DOCUMENT);
  private installed = false;

  install(): void {
    if (this.installed) {
      return;
    }
    this.installed = true;

    this.router.events.subscribe((event) => {
      if (event instanceof RoutesRecognized) {
        this.prepare(event.urlAfterRedirects);
        return;
      }
      if (event instanceof NavigationCancel || event instanceof NavigationError) {
        this.clear();
      }
    });
  }

  /** Marks the content area before the browser snapshots the outgoing page. */
  prepare(nextUrl: string): void {
    const direction = this.direction(this.router.url, nextUrl);
    if (!direction) {
      this.clear();
      return;
    }
    this.arm(direction);
  }

  onCreated(transition: PageViewTransition, from: RouteUrlNode, to: RouteUrlNode): void {
    const direction = this.direction(routeSnapshotPath(from), routeSnapshotPath(to));
    if (!direction) {
      transition.skipTransition();
      this.clear();
      return;
    }

    this.arm(direction);
    const clear = () => this.clear();
    void transition.finished.then(clear, clear);
  }

  private direction(fromPath: string, toPath: string): 'forward' | 'back' | null {
    if (this.prefersReducedMotion()) {
      return null;
    }
    return devicePageTransitionDirection(fromPath, toPath);
  }

  private arm(direction: 'forward' | 'back'): void {
    this.document.documentElement.dataset['pageTransition'] = direction;
    const content = this.contentElement();
    if (content) {
      content.style.viewTransitionName = PAGE_TRANSITION_NAME;
    }
  }

  private clear(): void {
    delete this.document.documentElement.dataset['pageTransition'];
    const content = this.contentElement();
    if (content) {
      content.style.viewTransitionName = '';
    }
  }

  private contentElement(): HTMLElement | null {
    return this.document.querySelector<HTMLElement>('.layout__content');
  }

  private prefersReducedMotion(): boolean {
    const matchMedia = this.document.defaultView?.matchMedia?.bind(this.document.defaultView);
    if (!matchMedia) {
      return false;
    }
    return matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
}
