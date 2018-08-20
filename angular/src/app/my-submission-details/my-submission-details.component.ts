import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SuccessMessage} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";

@Component({
  selector: 'app-my-submission-details',
  templateUrl: './my-submission-details.component.html',
  styleUrls: ['./my-submission-details.component.less']
})
export class MySubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;
  success: SuccessMessage;

  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  constructor(
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.loadingSubmission = true;
    this.submissionService.getMySubmission(this.submissionId).pipe(
      finalize(() => this.loadingSubmission = false)
    ).subscribe(
      submission => this.setupSubmission(submission),
      error => this.error = error.error
    )
  }

  ngOnDestroy(){
    clearInterval(this.timeTrackerHandler);
  }

  private setupSubmission(submission: Submission){
    this.submission = submission;

    if(moment().diff(moment(submission.created_at), 'seconds')<3)
      this.success = {msg: 'Submitted successfully'};

    const timeTracker = () => {
      this.createdFromNow = moment(submission.created_at).fromNow()
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 30000);
  }

}
