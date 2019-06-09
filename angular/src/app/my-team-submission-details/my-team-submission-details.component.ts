import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SuccessMessage, Task, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-my-team-submission-details',
  templateUrl: './my-team-submission-details.component.html',
  styleUrls: ['./my-team-submission-details.component.less']
})
export class MyTeamSubmissionDetailsComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;

  user: User;
  taskId: number;
  task: Task;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;
        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingSubmission = true;
            this.submissionService.getMyTeamSubmission(this.submissionId).pipe(
              finalize(() => this.loadingSubmission = false)
            ).subscribe(
              submission => this.setupSubmission(submission),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      },
      error=>this.error = error.error
    )
  }

  private setupSubmission(submission: Submission) {
    if (submission.task_id != this.taskId) {
      this.error = {msg: 'submission does not belong to this task'};
      return;
    }

    this.submission = submission;
    if (submission.submitter_id == this.user.id && moment().diff(moment(submission.created_at), 'seconds') < 3)
      this.success = {msg: 'Submitted successfully'};
  }

}
