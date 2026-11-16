import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PendingInviteService } from '@core/services';
import { BeginKeycloakAuthService, KeycloakAuthMode } from '@core/usecases';

@Component({
  selector: 'app-auth',
  standalone: true,
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.css',
})
export class AuthComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly pendingInvite = inject(PendingInviteService);
  private readonly beginAuth = inject(BeginKeycloakAuthService);

  ngOnInit(): void {
    const mode: KeycloakAuthMode =
      this.route.snapshot.queryParamMap.get('mode') === 'register' ? 'register' : 'login';
    void this.beginAuth.execute(mode, this.pendingInvite.getPostAuthPath());
  }
}
