import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, SuccessMessage, Task, Term, User} from "../models";
import {CategoryInfo, TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TitleService} from "../title.service";

@Component({
  selector: 'app-task-preview',
  templateUrl: './task-preview.component.html',
  styleUrls: ['./task-preview.component.less']
})
export class TaskPreviewComponent implements OnInit, OnDestroy {

  success: SuccessMessage;
  error: ErrorMessage;

  taskId: number;
  task: Task;
  loadingTask: boolean;
  category: CategoryInfo;

  user: User;
  termId: number;
  term: Term;
  accessRoles: Set<string>;
  timeTrackerHandler: number;

  printTaskTeamSize = TaskService.printTaskTeamSize;

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private taskService: TaskService,
    private route: ActivatedRoute,
    private router: Router,
    private titleService: TitleService
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;

        this.termId = parseInt(this.route.snapshot.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;
            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.taskId = parseInt(this.route.snapshot.paramMap.get('task_id'));
            this.loadingTask = true;
            this.taskService.getTaskPreview(this.taskId).pipe(
              finalize(() => this.loadingTask = false)
            ).subscribe(
              task => this.setupTask(task),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        );
      },
      error => this.error = error.error
    );
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
  }

  private setupTask(task: Task) {
    this.titleService.setTitle(`${task.title} (Preview)`, `${this.term.year}S${this.term.semester}`, this.term.course.code);

    if (task.term_id != this.termId) {
      this.error = {msg: `Task (id=${task.id}) is not a task of this term`};
      return;
    }

    this.task = task;
    this.category = TaskService.categories[task.type];

    const timeTracker = () => {
      if(moment(task.open_time).isSameOrBefore(moment.now())){
        this.router.navigate([`../../tasks/${this.taskId}`], {relativeTo: this.route, replaceUrl: true})
        return;
      }
      this.task['_open_time_from_now'] = task.open_time ? moment(task.open_time).fromNow() : null;
      this.task['_due_time_from_now'] = task.due_time ? moment(task.due_time).fromNow() : null;
    };
    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10000);
  }
}
