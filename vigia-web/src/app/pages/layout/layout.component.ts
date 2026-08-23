import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '@shared/components';
import { ToolbarComponent } from '@shared/components';
import { MessageComponent } from '@shared/components';
@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, SidebarComponent, ToolbarComponent, MessageComponent],
  standalone: true,
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.css',
})
export class LayoutComponent {}
