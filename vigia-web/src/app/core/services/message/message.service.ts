import { Injectable, signal } from '@angular/core';
import { Message } from '@core/interfaces';

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  messages = signal<Message | null>(null);

  addMessage(message: Message) {
    this.messages.set(message);
  }

  removeMessage() {
    this.messages.set(null);
  }

  getMessages() {
    return this.messages;
  }
}