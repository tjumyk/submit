import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Task, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import {TaskService} from "../task.service";
import {AdminService} from "../admin.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-submission-details',
  templateUrl: './submission-details.component.html',
  styleUrls: ['./submission-details.component.less']
})
export class SubmissionDetailsComponent implements OnInit {
  error: ErrorMessage;

  user: User;
  isAdmin: boolean = false;

  taskId: number;
  task: Task;
  userId: number;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  constructor(
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private accountService: AccountService,
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.userId = parseInt(this.route.snapshot.paramMap.get('user_id'));

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.route.paramMap.subscribe(
              paramMap=>{
                // reset
                this.submissionId = undefined;
                this.submission = undefined;

                // load
                this.submissionId = parseInt(paramMap.get('submission_id'));
                this.loadingSubmission = true;
                this.submissionService.getSubmission(this.submissionId).pipe(
                  finalize(() => this.loadingSubmission = false)
                ).subscribe(
                  submission => this.setupSubmission(submission),
                  error => this.error = error.error
                )
              }
            )
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  private setupSubmission(submission: Submission) {
    if (submission.submitter_id != this.userId) {
      this.error = {msg: 'submission does not belong to this user'};
      return;
    }
    if (submission.task_id != this.taskId) {
      this.error = {msg: 'submission does not belong to this task'};
      return;
    }

    this.submission = submission;
  }
}
