import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable, of} from "rxjs";
import {Submission, Task} from './models';
import {tap} from "rxjs/operators";

export class CategoryInfo{
  name: string;
  icon: string;
}

@Injectable({
  providedIn: 'root'
})
export class TaskService {
  private api = 'api/tasks';
  private cachedTasks : {[key: number]: Task} = {};

  constructor(
    private http: HttpClient
  ) { }

  static categories: {[key:string]: CategoryInfo} = {
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

  static printTaskTeamSize(task:Task): string{
    if(task.team_min_size != null){
      if(task.team_max_size != null){
        if(task.team_min_size==task.team_max_size)
          return task.team_min_size.toString();
        else
          return `${task.team_min_size}-${task.team_max_size}`
      }else{
        return `≥${task.team_min_size}`
      }
    }else{
      if(task.team_max_size != null)
        return `≤${task.team_max_size}`;
      else
        return 'no limit'
    }
  }

  getTask(id: number):Observable<Task>{
    return this.http.get<Task>(`${this.api}/${id}`).pipe(
      tap(task=>this.cachedTasks[task.id] = task)
    )
  }

  getCachedTask(id: number):Observable<Task>{
    const task = this.cachedTasks[id];
    if(task)
      return of(task);
    return this.getTask(id);
  }

  addSubmission(task_id: number, files: {[key:number]: File}):Observable<Submission>{
    const form = new FormData();
    for(let req_id in files){
      const file = files[req_id];
      if(file)
        form.append(req_id.toString(), file);
    }
    return this.http.post<Submission>(`${this.api}/${task_id}/my-submissions`, form)
  }

  getSubmissions(task_id: number): Observable<Submission[]>{
    return this.http.get<Submission[]>(`${this.api}/${task_id}/submissions`)
  }

  getMySubmissions(task_id: number): Observable<Submission[]>{
    return this.http.get<Submission[]>(`${this.api}/${task_id}/my-submissions`)
  }
}
