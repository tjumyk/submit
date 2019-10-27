import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {ErrorMessage, Submission, SubmissionFileDiff} from "../models";
import * as moment from "moment";
import {SubmissionService} from "../submission.service";
import {finalize} from "rxjs/operators";

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

  @Output()
  error: EventEmitter<ErrorMessage> = new EventEmitter();

  createdFromNow: string;
  timeTrackerHandler: number;

  loadingDiffs: boolean;
  diffs: {[fid: number]: SubmissionFileDiff};

  constructor(
    private submissionService: SubmissionService
  ) {
    this.apiBase = submissionService.api; // this default api is only for admins or tutors
  }

  ngOnInit() {
    if(!this.submission)
      return;

    const timeTracker = () => {
      this.createdFromNow = moment(this.submission.created_at).fromNow()
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 30000);

    this.loadingDiffs = true;
    this.submissionService.getDiffs(this.submission.id, this.apiBase).pipe(
      finalize(()=>this.loadingDiffs = false)
    ).subscribe(
      diffs=>this.diffs = diffs,
      error=>this.error.emit(error.error)
    )
  }

  ngOnDestroy(): void {
    clearInterval(this.timeTrackerHandler);
  }

}
