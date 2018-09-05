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

export class LatePenaltySegment {
  fromDay: number;
  toDay?: number;
  days?: number;
  penaltyPerDay: number;
}

export class LatePenalty {
  readonly segments: LatePenaltySegment[];

  constructor(segments: LatePenaltySegment[]) {
    this.segments = segments;
  }

  getPenalty(days: number): number{
    if(!this.segments || this.segments.length == 0)
      return null;
    let penalty = 0;
    let segmentIndex = 0;
    while(days && segmentIndex < this.segments.length){
      const segment = this.segments[segmentIndex++];
      if(segment.days == null || days <= segment.days){
        penalty += segment.penaltyPerDay * days;
        break;
      }
      penalty += segment.penaltyPerDay * segment.days;
      days -= segment.days;
    }
    penalty = Math.min(1.0, penalty);
    return penalty;
  }

  static parse(expression: string): LatePenalty {
    if (!expression)
      return null;
    expression = expression.trim();
    if (!expression)
      return null;

    const segments: LatePenaltySegment[] = [];

    const penalties: number[] = [];
    for (let part of expression.split(/\s+/)) {
      const num = parseFloat(part);
      if(isNaN(num) || num < 0){
        throw `Invalid item in late penalty list: ${part}`;
      }
      penalties.push(num)
    }
    if (penalties.length == 0) {
      return null;
    }

    let index: number = 0;
    let day: number = 1;
    let fromDay: number = 0;
    let lastPenalty: number = null;
    let samePenaltyDays: number = 0;
    let accumulativePenalty: number = 0.0;

    while (true) {
      const penalty = penalties[index];
      accumulativePenalty += penalty;

      if (lastPenalty === null) { // first penalty
        lastPenalty = penalty;
        fromDay = day;
        samePenaltyDays = 1;
      } else {
        if (penalty == lastPenalty) {
          ++samePenaltyDays;
        } else {
          segments.push({
            fromDay: fromDay,
            toDay: fromDay + samePenaltyDays - 1,
            days: samePenaltyDays,
            penaltyPerDay: lastPenalty
          });
          lastPenalty = penalty;
          fromDay = day;
          samePenaltyDays = 1;
        }
      }

      if (Math.abs(accumulativePenalty - 1.0) < 1.0e-6) {
        break;
      }

      if (accumulativePenalty > 1.0) { // fix last day
        if (samePenaltyDays > 1) {
          --samePenaltyDays;
          segments.push({
            fromDay: fromDay,
            toDay: fromDay + samePenaltyDays - 1,
            penaltyPerDay: lastPenalty,
            days: samePenaltyDays
          });
        }

        lastPenalty -= accumulativePenalty - 1.0;
        fromDay = day;
        samePenaltyDays = 1;
        accumulativePenalty = 1.0;
        break;
      }

      // accumulative penalty must be less than 1.0 here
      if (index < penalties.length - 1) {
        ++index;
      } else {
        // keep index at the last position after list exhausted
        if (penalty == 0) {
          break; // but if last penalty is 0, stop now to avoid infinite loop
        }
      }
      ++day;
    }

    // remaining days
    if (samePenaltyDays) {
      if (lastPenalty == 0) {
        segments.push({ // endless segment
          fromDay: fromDay,
          penaltyPerDay: lastPenalty
        });
      } else {
        segments.push({
          fromDay: fromDay,
          toDay: fromDay + samePenaltyDays - 1,
          days: samePenaltyDays,
          penaltyPerDay: lastPenalty
        });
      }
    }

    return new LatePenalty(segments)
  }
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
