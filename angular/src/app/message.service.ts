import {Injectable} from '@angular/core';
import {Message, MessageChannel} from "./models";
import {Observable} from "rxjs";
import {HttpClient} from "@angular/common/http";

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private api = 'api/messages';

  constructor(
    private http: HttpClient
  ) {
  }

  getById(mid: number): Observable<Message> {
    return this.http.get<Message>(`${this.api}/${mid}`)
  }

  markRead(mid: number): Observable<any> {
    return this.http.get(`${this.api}/${mid}/mark-read`)
  }

  getChannels(): Observable<MessageChannel[]> {
    return this.http.get<MessageChannel[]>(`${this.api}/channels`)
  }

  subscribeChannel(channel_id: number): Observable<any> {
    return this.http.get(`${this.api}/channels/${channel_id}/subscribe`)
  }

  unsubscribeChannel(channel_id: number): Observable<any> {
    return this.http.get(`${this.api}/channels/${channel_id}/unsubscribe`)
  }
}
