import { Injectable } from '@angular/core'
import { HttpClient } from '@angular/common/http'

@Injectable({
  providedIn: 'root',
})
export class AppService {
  messageArray: any[] = []

  constructor(private httpClient: HttpClient) {}

  query(data: any) {
    let url = 'http://34.130.215.234:9000/query'
    return this.httpClient.post(url, data)
  }
  stats() {
    let url = 'http://34.130.215.234:9000/stats'
    return this.httpClient.get(url)
  }
  sentiment_history() {
    let url = 'http://34.130.215.234:9000/sentiment_history'
    return this.httpClient.get(url)
  }
}
