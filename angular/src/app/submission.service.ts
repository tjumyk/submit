import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {Submission} from "./models";

@Injectable({
  providedIn: 'root'
})
export class SubmissionService {
  private api = 'api/submissions';
  private myApi = 'api/my-submissions';
  private myTeamApi = 'api/my-team-submissions';

  constructor(
    private http: HttpClient
  ) { }

  getSubmission(id: number):Observable<Submission>{
    return this.http.get<Submission>(`${this.api}/${id}`)
  }

  getMySubmission(id: number):Observable<Submission>{
    return this.http.get<Submission>(`${this.myApi}/${id}`)
  }

  getMyTeamSubmission(id: number):Observable<Submission>{
    return this.http.get<Submission>(`${this.myTeamApi}/${id}`)
  }
}
