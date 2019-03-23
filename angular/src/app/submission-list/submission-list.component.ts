import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task, User} from "../models";
import {AccountService} from "../account.service";
import {LastAutoTestsMap, TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-submission-list',
  templateUrl: './submission-list.component.html',
  styleUrls: ['./submission-list.component.less']
})
export class SubmissionListComponent implements OnInit {

  error: ErrorMessage;

  taskId: number;
  task: Task;
  userId: number;
  user: User;
  status: SubmissionStatus;
  submissions: Submission[];
  loadingUser: boolean;
  loadingStatus: boolean;
  loadingSubmissions: boolean;
  lastAutoTests: LastAutoTestsMap;
  loadingLastAutoTests: boolean;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.userId = parseInt(this.route.snapshot.paramMap.get('user_id'));

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingUser = true;
        this.taskService.getUser(this.taskId, this.userId).pipe(
          finalize(() => this.loadingUser = false)
        ).subscribe(
          user => {
            this.user = user;

            this.loadingStatus = true;
            this.taskService.getUserSubmissionStatus(this.taskId, this.userId).pipe(
              finalize(() => this.loadingStatus = false)
            ).subscribe(
              status => {
                this.status = status;

                this.loadingSubmissions = true;
                this.taskService.getUserSubmissions(this.taskId, this.userId).pipe(
                  finalize(() => this.loadingSubmissions = false)
                ).subscribe(
                  submissions => {
                    this.submissions = submissions;

                    this.loadingLastAutoTests = true;
                    this.taskService.getUserSubmissionLastAutoTests(this.taskId, this.userId).pipe(
                      finalize(()=>this.loadingLastAutoTests=false)
                    ).subscribe(
                      tests=>this.lastAutoTests = tests,
                      error=>this.error = error.error
                    )
                  },
                  error => this.error = error.error
                )
              },
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    );
  }

}
