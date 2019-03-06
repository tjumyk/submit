import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {AutoTest, Submission} from "./models";

@Injectable({
  providedIn: 'root'
})
export class SubmissionService {
  private api = 'api/submissions';
  private myApi = 'api/my-submissions';
  private myTeamApi = 'api/my-team-submissions';

  constructor(
    private http: HttpClient
  ) {
  }

  getAutoTestStatusColor(status: string): string{
    switch (status) {
      case 'STARTED': return '#21ba45';
      case 'SUCCESS': return '#21ba45';
      case 'RETRY': return '#fbbd08';
      case 'FAILURE': return '#db2828';
      case 'REVOKED': return '#db2828';
      default: return 'rgba(0,0,0,.87)';
    }
  }

  getSubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.api}/${id}`)
  }

  getMySubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.myApi}/${id}`)
  }

  getMyTeamSubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.myTeamApi}/${id}`)
  }

  getAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.api}/${id}/auto-tests`)
  }

  getMyAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.myApi}/${id}/auto-tests`)
  }

  getMyTeamAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.myTeamApi}/${id}/auto-tests`)
  }
}
