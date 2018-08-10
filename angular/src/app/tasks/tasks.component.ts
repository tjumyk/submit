import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Task, Team, Term, User} from "../models";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";

@Component({
  selector: 'app-tasks',
  templateUrl: './tasks.component.html',
  styleUrls: ['./tasks.component.less']
})
export class TasksComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  termId: number;

  tasks: Task[];
  loadingTasks: boolean;
  taskCategories: {[key: string]: Task[]} = {};

  user: User;
  term: Term;
  accessRoles: Set<string>;
  categories = TaskService.categories;

  printTaskTeamSize = TaskService.printTaskTeamSize;

  timeTrackerHandler: number;

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    moment.locale('en-AU');

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;

        this.termId = parseInt(this.route.snapshot.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term=>{
            this.term = term;
            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.loadingTasks = true;
            this.termService.getTasks(this.termId).pipe(
              finalize(() => this.loadingTasks = false)
            ).subscribe(
              tasks => this.setupTasks(tasks),
              error => this.error = error.error
            )
          },
          error=>this.error =error.error
        );
      },
      error=>this.error=error.error
    );
  }

  ngOnDestroy(){
    clearTimeout(this.timeTrackerHandler);
  }

  private setupTasks(tasks: Task[]){
    this.tasks = tasks;

    for(let task of tasks){
      let list = this.taskCategories[task.type];
      if(list == undefined){
        list = [];
        this.taskCategories[task.type] = list;
      }
      list.push(task);
    }

    const allowPreview = this.accessRoles.has('admin') || this.accessRoles.has('tutor');

    const timeTracker = ()=>{
      const now = moment.now();
      for(let task of tasks){
        task['_accessible'] = allowPreview || moment(task.open_time).isSameOrBefore(now);
        task['_open_time_from_now'] = task.open_time ? moment(task.open_time).fromNow() : null;
        task['_due_time_from_now'] = task.due_time ? moment(task.due_time).fromNow() : null;
        task['_close_time_from_now'] = task.close_time ? moment(task.close_time).fromNow() : null;
      }
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10000);
  }
}
