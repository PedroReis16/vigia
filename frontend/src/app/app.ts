import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { MonitorVigiaComponent } from './monitor-vigia/monitor-vigia.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, MonitorVigiaComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('Vigia');
}
