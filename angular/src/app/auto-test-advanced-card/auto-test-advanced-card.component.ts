import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {AutoTest, AutoTestConfig, ErrorMessage, Submission} from "../models";
import {SubmissionService} from "../submission.service";
import {finalize} from "rxjs/operators";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-auto-test-advanced-card',
  templateUrl: './auto-test-advanced-card.component.html',
  styleUrls: ['./auto-test-advanced-card.component.less'],
  host: {'class': 'ui segment'}
})
export class AutoTestAdvancedCardComponent implements OnInit {
  @Input() test: AutoTest;
  @Input() config: AutoTestConfig;
  @Input() submission: Submission;
  @Input() isAdmin: boolean;
  @Output() deleted: EventEmitter<any> = new EventEmitter();
  @Output() error: EventEmitter<ErrorMessage> = new EventEmitter();

  getStatusColor: (status: string) => string;
  printConclusion: (test: AutoTest, config: AutoTestConfig) => any;
  renderResultHTML: (test: AutoTest, config: AutoTestConfig) => string;

  constructor(
    private adminService: AdminService,
    private submissionService: SubmissionService
  ) {
    /* use closures to avoid scope error */
    this.getStatusColor = status => submissionService.getAutoTestStatusColor(status);
    this.printConclusion = (test, config) => submissionService.printConclusion(test, config);
    this.renderResultHTML = (test, config) => submissionService.renderResultHTML(test, config);
  }

  ngOnInit() {
  }

  deleteAutoTest(test: AutoTest, btn: HTMLElement) {
    if (!confirm(`Really want to delete test ${test.id}?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteAutoTest(this.submission.id, test.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.deleted.emit(null),
      error => this.error.emit(error.error)
    )
  }

}
