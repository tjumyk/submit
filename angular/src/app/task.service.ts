import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable, of} from "rxjs";
import {
  Submission,
  SubmissionStatus,
  Task,
  Team,
  TeamSubmissionSummary,
  User,
  UserSubmissionSummary,
  UserTeamAssociation
} from './models';
import {map, tap} from "rxjs/operators";

export class CategoryInfo {
  name: string;
  icon: string;
}

export class NewTeamForm {
  name: string;
  slogan?: string;
}

@Injectable({
  providedIn: 'root'
})
export class TaskService {
  private api = 'api/tasks';
  private cachedTasks: { [key: number]: Task } = {};
  private cachedTaskPreviews: { [key: number]: Task } = {};

  constructor(
    private http: HttpClient
  ) {
  }

  static categories: { [key: string]: CategoryInfo } = {
    lab: {
      name: 'Labs',
      icon: 'flask'
    },
    assignment: {
      name: 'Assignments',
      icon: 'file alternate outline'
    },
    project: {
      name: 'Projects',
      icon: 'wrench'
    }
  };

  static printTaskTeamSize(task: Task): string {
    if (task.team_min_size != null) {
      if (task.team_max_size != null) {
        if (task.team_min_size == task.team_max_size)
          return task.team_min_size.toString();
        else
          return `${task.team_min_size}-${task.team_max_size}`
      } else {
        return `≥${task.team_min_size}`
      }
    } else {
      if (task.team_max_size != null)
        return `≤${task.team_max_size}`;
      else
        return 'no limit'
    }
  }

  getTask(id: number): Observable<Task> {
    return this.http.get<Task>(`${this.api}/${id}`).pipe(
      tap(task => this.cachedTasks[task.id] = task)
    )
  }

  getCachedTask(id: number): Observable<Task> {
    const task = this.cachedTasks[id];
    if (task)
      return of(task);
    return this.getTask(id);
  }

  getTaskPreview(id: number): Observable<Task> {
    const params = new HttpParams().append('preview', 'true');
    return this.http.get<Task>(`${this.api}/${id}`, {params: params}).pipe(
      tap(task => this.cachedTaskPreviews[task.id] = task)
    )
  }

  getCachedTaskPreview(id: number): Observable<Task> {
    const task = this.cachedTaskPreviews[id];
    if (task)
      return of(task);
    return this.getTaskPreview(id);
  }

  addSubmission(task_id: number, files: { [key: number]: File }): Observable<Submission> {
    const form = new FormData();
    for (let req_id in files) {
      const file = files[req_id];
      if (file)
        form.append(req_id.toString(), file);
    }
    return this.http.post<Submission>(`${this.api}/${task_id}/my-submissions`, form)
  }

  getUserSubmissionSummaries(task_id: number): Observable<UserSubmissionSummary[]> {
    return this.http.get<UserSubmissionSummary[]>(`${this.api}/${task_id}/user-submission-summaries`)
  }

  getTeamSubmissionSummaries(task_id: number): Observable<TeamSubmissionSummary[]> {
    return this.http.get<TeamSubmissionSummary[]>(`${this.api}/${task_id}/team-submission-summaries`)
  }

  getUserSubmissions(task_id: number, user_id: number): Observable<Submission[]> {
    return this.http.get<Submission[]>(`${this.api}/${task_id}/user-submissions/${user_id}`)
  }

  getUser(task_id: number, user_id: number): Observable<User> {
    return this.http.get<User>(`${this.api}/${task_id}/users/${user_id}`)
  }

  getTeamSubmissions(task_id: number, team_id: number): Observable<Submission[]> {
    return this.http.get<Submission[]>(`${this.api}/${task_id}/team-submissions/${team_id}`)
  }

  getMySubmissions(task_id: number): Observable<Submission[]> {
    return this.http.get<Submission[]>(`${this.api}/${task_id}/my-submissions`)
  }

  getMyTeamSubmissions(task_id: number): Observable<Submission[]> {
    return this.http.get<Submission[]>(`${this.api}/${task_id}/my-team-submissions`)
  }

  getMyTeamAssociation(task_id: number): Observable<UserTeamAssociation> {
    return this.http.get<UserTeamAssociation>(`${this.api}/${task_id}/my-team-association`)
  }

  getTeams(task_id: number): Observable<Team[]> {
    return this.http.get<[Team, number][]>(`${this.api}/${task_id}/teams`).pipe(
      map(records => {
        const teams = [];
        for (let record of records) {
          const team = record[0];
          team.total_user_associations = record[1];
          teams.push(team)
        }
        return teams
      })
    )
  }

  addTeam(task_id: number, form: NewTeamForm): Observable<Team> {
    return this.http.post<Team>(`${this.api}/${task_id}/teams`, form)
  }

  getMySubmissionStatus(task_id: number): Observable<SubmissionStatus> {
    return this.http.get<SubmissionStatus>(`${this.api}/${task_id}/my-submission-status`)
  }

  getMyTeamSubmissionStatus(task_id: number): Observable<SubmissionStatus> {
    return this.http.get<SubmissionStatus>(`${this.api}/${task_id}/my-team-submission-status`)
  }
}
