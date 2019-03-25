import {Component, Input, OnInit} from '@angular/core';
import {AutoTest, AutoTestConfig} from "../models";
import {SubmissionService} from "../submission.service";
import {printDuration} from "../time-util";
import * as moment from "moment";

@Component({
  selector: 'app-auto-test-card',
  templateUrl: './auto-test-card.component.html',
  styleUrls: ['./auto-test-card.component.less'],
  host: {'class': 'ui segment'}
})
export class AutoTestCardComponent implements OnInit {
  @Input() test: AutoTest;
  @Input() config: AutoTestConfig;

  getStatusColor: (status: string) => string;
  extractConclusion: (test: AutoTest, config: AutoTestConfig) => any;
  renderResultHTML: (test: AutoTest, config: AutoTestConfig) => string;

  constructor(
    private submissionService: SubmissionService
  ) {
    /* use closures to avoid scope error */
    this.getStatusColor = status => submissionService.getAutoTestStatusColor(status);
    this.extractConclusion = (test, config) => submissionService.extractConclusion(test, config);
    this.renderResultHTML = (test, config) => submissionService.renderResultHTML(test, config);
  }

  ngOnInit() {
  }

  computeDuration(start_time, end_time) {
    return printDuration(moment(end_time).diff(moment(start_time), 'seconds'))
  }

}
