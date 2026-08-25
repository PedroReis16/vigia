import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '@shared/components';
import { ToolbarComponent } from '@shared/components';
import { MessageComponent } from '@shared/components';
import { DeviceGroupsRealtimeService } from '@core/services';

@Component({
  selector: 'app-layout',
  imports: [RouterOutlet, SidebarComponent, ToolbarComponent, MessageComponent],
  standalone: true,
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.css',
})
export class LayoutComponent implements OnInit, OnDestroy {
  private readonly realtime = inject(DeviceGroupsRealtimeService);

  ngOnInit(): void {
    void this.realtime.connect();
  }

  ngOnDestroy(): void {
    void this.realtime.disconnect();
  }
}
