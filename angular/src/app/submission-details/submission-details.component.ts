import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Task} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";

@Component({
  selector: 'app-submission-details',
  templateUrl: './submission-details.component.html',
  styleUrls: ['./submission-details.component.less']
})
export class SubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  taskId: number;
  userId: number;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  constructor(
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.userId = parseInt(this.route.snapshot.paramMap.get('user_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.loadingSubmission = true;
    this.submissionService.getSubmission(this.submissionId).pipe(
      finalize(() => this.loadingSubmission = false)
    ).subscribe(
      submission => this.setupSubmission(submission),
      error => this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
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

    const timeTracker = () => {
      this.createdFromNow = moment(submission.created_at).fromNow()
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 30000);
  }
}
