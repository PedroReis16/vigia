import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Oauth2Service } from '@core/services';

@Component({
  selector: 'app-callback',
  standalone: true,
  template: `<p>Completing authentication…</p>`,
})
export class CallbackComponent implements OnInit {
  private readonly oauth2Service = inject(Oauth2Service);
  private readonly router = inject(Router);

  async ngOnInit(): Promise<void> {
    await this.oauth2Service.handleCallback();
    await this.router.navigate(['/']);
  }
}
