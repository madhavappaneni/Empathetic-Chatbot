import { Component, OnInit } from '@angular/core'
import { AppService } from '../app.service'

@Component({
  selector: 'app-chat',
  templateUrl: './chat-new.component.html',
  styleUrls: ['./chat-new.component.css'],
})
export class ChatNewComponent implements OnInit {
  title = 'IR Chatbot'
  topic: string = 'All'
  message = ''


  constructor(public appService: AppService) {}

  ngOnInit() {}

  sendMessage() {
    const data = { query: this.message, topic: this.topic.toLowerCase() }
    this.appService.messageArray.push({ name: 'user', message: this.message })
    this.appService.query(data).subscribe((response: any) => {
      this.appService.messageArray.push({ name: 'bot', message: response.response })
    })
    this.message = ''
  }

  reset_filter() {
    this.topic = 'all'
  }
}
