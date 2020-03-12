import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable, of} from "rxjs";
import {FinalMarks, Message, Task, Term, User} from "./models";
import {tap} from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class TermService {
  private api = 'api/terms';
  private termCaches: {[key: number]: Term} = {};
  private tasksCaches: { [key: number]: Task[] } = {};

  private _messageRefreshPeriod = 2 * 60 * 1000;
  get messageRefreshPeriod(){
    return this._messageRefreshPeriod;
  }

  private _enableMessageRefresh: boolean;
  private disableMessageRefreshKey = 'submit_disable_message_refresh';
  get enableMessageRefresh(){
    return this._enableMessageRefresh;
  }
  set enableMessageRefresh(enabled: boolean){
    this._enableMessageRefresh = enabled;
    // persist setting in local storage
    if(enabled)
      window.localStorage.removeItem(this.disableMessageRefreshKey);
    else
      window.localStorage.setItem(this.disableMessageRefreshKey, 'true')
  }

  // A global trigger to enforce an instant update to the unread count of the messages
  unreadMessagesCountTrigger = () => undefined;

  constructor(
    private http: HttpClient
  ) {
    // get settings from local storage
    this._enableMessageRefresh = window.localStorage.getItem(this.disableMessageRefreshKey) !== 'true'
  }

  static getAccessRoles(term:Term, user:User):Set<string>{
    if(!term || !user)
      return null;
    const roles = new Set<string>();
    for(let g of user.groups){
      if(g.name == 'admin')
        roles.add('admin');
      if(g.id == term.student_group_id)
        roles.add('student');
      if(g.id == term.course.tutor_group_id)
        roles.add('tutor')
    }
    return roles;
  }

  getTerm(id: number):Observable<Term>{
    return this.http.get<Term>(`${this.api}/${id}`).pipe(
      tap(term=>this.termCaches[term.id] = term)
    )
  }

  getCachedTerm(id: number): Observable<Term>{
    const term = this.termCaches[id];
    if(term)
      return of(term);
    return this.getTerm(id);
  }

  getTasks(term_id: number): Observable<Task[]>{
    return this.http.get<Task[]>(`${this.api}/${term_id}/tasks`).pipe(
      tap(tasks => this.tasksCaches[term_id] = tasks)
    )
  }

  getCachedTasks(term_id: number): Observable<Task[]> {
    const tasks = this.tasksCaches[term_id];
    if (tasks)
      return of(tasks);
    return this.getTasks(term_id);
  }

  getMessages(term_id: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.api}/${term_id}/messages`)
  }

  getMessagesAfterId(term_id: number, message_id: number): Observable<Message[]> {
    let params = new HttpParams().append('after_id', message_id.toString());
    return this.http.get<Message[]>(`${this.api}/${term_id}/messages`, {params: params})
  }

  getUnreadMessagesCount(term_id: number): Observable<number> {
    return this.http.get<number>(`${this.api}/${term_id}/unread-messages-count`)
  }

  markAllMessagesRead(term_id: number): Observable<any>{
    return this.http.get(`${this.api}/${term_id}/mark-all-messages-read`)
  }

  getStudents(term_id: number): Observable<User[]>{
    return this.http.get<User[]>(`${this.api}/${term_id}/students`)
  }

  getMyFinalMarks(term_id: number): Observable<FinalMarks[]>{
    return this.http.get<FinalMarks[]>(`${this.api}/${term_id}/my-final-marks`)
  }
}
