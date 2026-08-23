import { Component, inject, OnInit } from '@angular/core';
import { Oauth2Service } from '@core/services';

@Component({
  selector: 'app-login',
  standalone: true,
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  private readonly oauth2Service = inject(Oauth2Service);

  ngOnInit(): void {
    void this.oauth2Service.login();
  }
}
