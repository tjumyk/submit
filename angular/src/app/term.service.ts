import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable, of} from "rxjs";
import {Term, Task, User} from "./models";
import {tap} from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class TermService {
  private api = 'api/terms';
  private termCaches: {[key: number]: Term} = {};

  constructor(
    private http: HttpClient
  ) { }

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
    return this.http.get<Task[]>(`${this.api}/${term_id}/tasks`)
  }
}
