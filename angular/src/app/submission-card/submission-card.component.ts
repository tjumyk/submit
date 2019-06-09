import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {Submission} from "../models";
import * as moment from "moment";
import {SubmissionService} from "../submission.service";

@Component({
  selector: 'app-submission-card',
  templateUrl: './submission-card.component.html',
  styleUrls: ['./submission-card.component.less'],
  host: {'class': 'ui segment'}
})
export class SubmissionCardComponent implements OnInit, OnDestroy {
  @Input()
  submission: Submission;

  @Input()
  apiBase: string;

  createdFromNow: string;
  timeTrackerHandler: number;

  constructor(
    private submissionService: SubmissionService
  ) {
    this.apiBase = submissionService.api; // this default api is only for admins or tutors
  }

  ngOnInit() {
    const timeTracker = () => {
      this.createdFromNow = moment(this.submission.created_at).fromNow()
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 30000);
  }

  ngOnDestroy(): void {
    clearInterval(this.timeTrackerHandler);
  }

}
