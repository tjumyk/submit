import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {finalize} from "rxjs/operators";
import {ErrorMessage, Submission, SubmissionFileDiff} from "../models";
import {SubmissionService} from "../submission.service";

@Component({
  selector: 'app-submission-diff-view',
  templateUrl: './submission-diff-view.component.html',
  styleUrls: ['./submission-diff-view.component.less']
})
export class SubmissionDiffViewComponent implements OnInit {
  @Input()
  submission: Submission;
  @Input()
  apiBase: string;

  @Output()
  error: EventEmitter<ErrorMessage> = new EventEmitter();

  loadingDiffs: boolean;
  diffs: SubmissionFileDiff[];

  constructor(private submissionService: SubmissionService) {
    this.apiBase = submissionService.api; // this default api is only for admins or tutors
  }

  ngOnInit() {
    if(!this.submission)
      return;

    this.loadingDiffs = true;
    this.submissionService.getDiffs(this.submission.id, this.apiBase).pipe(
      finalize(()=>this.loadingDiffs=false)
    ).subscribe(
      diffs=>this.diffs = diffs,
      error=>this.error.emit(error.error)
    )
  }

}
