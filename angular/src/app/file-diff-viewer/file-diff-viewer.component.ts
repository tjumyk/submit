import {Component, Input, OnInit} from '@angular/core';
import {SubmissionFileDiff} from "../models";

@Component({
  selector: 'app-file-diff-viewer',
  templateUrl: './file-diff-viewer.component.html',
  styleUrls: ['./file-diff-viewer.component.less'],
  host: {'class': 'ui segment'}
})
export class FileDiffViewerComponent implements OnInit {
  @Input()
  diff: SubmissionFileDiff;

  expanded: boolean = false;

  constructor() {
  }

  ngOnInit() {
  }

}
