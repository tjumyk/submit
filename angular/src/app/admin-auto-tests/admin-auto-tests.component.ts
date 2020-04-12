import {Component, OnDestroy, OnInit} from '@angular/core';
import {AutoTestSummaries, ErrorMessage} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";
import {TitleService} from "../title.service";
import {AutoTestConfigTypeInfo, SubmissionService} from "../submission.service";

@Component({
  selector: 'app-admin-auto-tests',
  templateUrl: './admin-auto-tests.component.html',
  styleUrls: ['./admin-auto-tests.component.less']
})
export class AdminAutoTestsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  autoTestConfigTypes: { [id: string]: AutoTestConfigTypeInfo };

  loading: boolean;
  summaries: AutoTestSummaries;

  updateInterval: number = 30000;  // 30s
  updateHandler: number;

  constructor(private adminService: AdminService,
              private titleService: TitleService,
              private submissionService: SubmissionService) {
  }

  ngOnInit() {
    this.titleService.setTitle('Auto Tests', 'Management');
    this.autoTestConfigTypes = this.submissionService.autoTestConfigTypes;

    this.updateHandler = setInterval(() => {
      this.update()
    }, this.updateInterval);
    this.update()
  }

  ngOnDestroy(): void {
    if (this.updateHandler)
      clearInterval(this.updateHandler)
  }

  update() {
    this.loading = true;
    this.adminService.getAutoTestSummaries().pipe(
      finalize(() => this.loading = false)
    ).subscribe(
      summaries => this.summaries = summaries,
      error => {
        clearInterval(this.updateHandler);
        this.error = error.error;
      }
    )
  }

}
