import {Component, Input, OnInit} from '@angular/core';
import {SubmissionFileDiff} from "../models";
import {SubmissionService} from "../submission.service";

@Component({
  selector: 'app-file-diff-label',
  templateUrl: './file-diff-label.component.html',
  styleUrls: ['./file-diff-label.component.less']
})
export class FileDiffLabelComponent implements OnInit {
  @Input()
  diff: SubmissionFileDiff;
  @Input()
  apiBase: string;

  constructor(private submissionService: SubmissionService) {
    this.apiBase = submissionService.api;
  }

  ngOnInit() {
  }

}
