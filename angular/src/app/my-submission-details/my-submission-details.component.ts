import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SuccessMessage, Task} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";

@Component({
  selector: 'app-my-submission-details',
  templateUrl: './my-submission-details.component.html',
  styleUrls: ['./my-submission-details.component.less']
})
export class MySubmissionDetailsComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;

  taskId: number;
  task: Task;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  constructor(
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingSubmission = true;
        this.submissionService.getMySubmission(this.submissionId).pipe(
          finalize(() => this.loadingSubmission = false)
        ).subscribe(
          submission => this.setupSubmission(submission),
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  private setupSubmission(submission: Submission) {
    this.submission = submission;

    if (moment().diff(moment(submission.created_at), 'seconds') < 3)
      this.success = {msg: 'Submitted successfully'};
  }

}
