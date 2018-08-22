import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Task, Term, User} from "../models";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-task-details-preview',
  templateUrl: './task-details-preview.component.html',
  styleUrls: ['./task-details-preview.component.less']
})
export class TaskDetailsPreviewComponent implements OnInit {

  error: ErrorMessage;

  taskId: number;
  task: Task;
  user: User;
  termId: number;
  term: Term;
  accessRoles: Set<string>;

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;

        this.termId = parseInt(this.route.snapshot.parent.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;
            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));
            this.taskService.getCachedTaskPreview(this.taskId).subscribe(
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

  private setupTask(task: Task) {
    this.task = task;
  }

}
