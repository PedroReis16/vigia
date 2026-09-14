import { Component, effect, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthExitTransitionService, ThemeService } from '@core/services';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  standalone: true,
})
export class AppComponent {
  title = 'vigia-web';

  /** Eager init so light/dark tokens apply on every route (not only Home). */
  private readonly themeService = inject(ThemeService);
  readonly authExitTransition = inject(AuthExitTransitionService);

  constructor() {
    effect(() => {
      if (typeof document === 'undefined') {
        return;
      }
      document.documentElement.classList.toggle(
        'auth-transition-bridge',
        this.authExitTransition.bridgeActive(),
      );
    });
  }
}
