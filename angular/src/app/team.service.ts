import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {Team} from "./models";

export class UpdateTeamForm {
  slogan: string;
}

@Injectable({
  providedIn: 'root'
})
export class TeamService {
  private api = 'api/teams';

  constructor(
    private http: HttpClient
  ) {
  }

  getTeam(id: number): Observable<Team> {
    return this.http.get<Team>(`${this.api}/${id}`)
  }

  updateTeam(id: number, form: UpdateTeamForm): Observable<Team> {
    return this.http.put<Team>(`${this.api}/${id}`, form)
  }

  dismissTeam(id: number): Observable<any> {
    return this.http.delete(`${this.api}/${id}`)
  }

  invite(team_id: number, user_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/invite/${user_id}`, null)
  }

  cancelInvitation(team_id: number, user_id: number): Observable<any> {
    return this.http.delete(`${this.api}/${team_id}/invite/${user_id}`)
  }

  acceptInvitation(team_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/handle-invite`, null)
  }

  rejectInvitation(team_id: number, user_id: number): Observable<any> {
    return this.http.delete(`${this.api}/${team_id}/handle-invite`)
  }

  applyJoin(team_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/join`, null)
  }

  cancelJoinApplication(team_id: number): Observable<any> {
    return this.http.delete(`${this.api}/${team_id}/join`)
  }

  acceptJoinApplication(team_id: number, applicant_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/handle-join/${applicant_id}`, null)
  }

  rejectJoinApplication(team_id: number, applicant_id: number): Observable<any> {
    return this.http.delete(`${this.api}/${team_id}/handle-join/${applicant_id}`)
  }

  leaveTeam(team_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/leave`, null)
  }

  kickOut(team_id: number, user_id: number) {
    return this.http.put(`${this.api}/${team_id}/kick-out/${user_id}`, null)
  }

  finaliseTeam(team_id: number): Observable<any> {
    return this.http.put(`${this.api}/${team_id}/finalise`, null)
  }

}
