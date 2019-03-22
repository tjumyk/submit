import {Component, Input, OnInit} from '@angular/core';
import {AutoTest, AutoTestConfig} from "../models";
import {SubmissionService} from "../submission.service";

@Component({
  selector: 'app-auto-test-mini-card',
  templateUrl: './auto-test-mini-card.component.html',
  styleUrls: ['./auto-test-mini-card.component.less']
})
export class AutoTestMiniCardComponent implements OnInit {
  @Input() test: AutoTest;
  @Input() config: AutoTestConfig;

  getStatusColor: (status: string) => string;
  printConclusion: (test: AutoTest, config: AutoTestConfig) => any;

  constructor(
    private submissionService: SubmissionService
  ) {
    /* use closures to avoid scope error */
    this.getStatusColor = status => submissionService.getAutoTestStatusColor(status);
    this.printConclusion = (test, config) => submissionService.printConclusion(test, config);
  }

  ngOnInit() {
  }

}
