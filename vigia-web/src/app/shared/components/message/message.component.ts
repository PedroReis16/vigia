import { NgIf } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MessageService } from '@core/services/message/message.service';
import { ButtonModule } from '@openng/optimus-ui/button';
import { MessageModule } from '@openng/optimus-ui/message';
@Component({
  selector: 'app-message',
  imports: [MessageModule, NgIf, ButtonModule],
  standalone: true,
  templateUrl: './message.component.html',
  styleUrl: './message.component.css',
})
export class MessageComponent {
  public readonly messageService = inject(MessageService);
  message = this.messageService.getMessages();

  removeMessage() {
    setTimeout(() => {
      this.messageService.removeMessage();
    }, 1000);
  }
}
