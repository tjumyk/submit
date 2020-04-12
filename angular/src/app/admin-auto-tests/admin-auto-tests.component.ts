import {Component, OnInit} from '@angular/core';
import {AutoTestSummaries, ErrorMessage} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";
import {TitleService} from "../title.service";

@Component({
  selector: 'app-admin-auto-tests',
  templateUrl: './admin-auto-tests.component.html',
  styleUrls: ['./admin-auto-tests.component.less']
})
export class AdminAutoTestsComponent implements OnInit {
  error: ErrorMessage;

  loading: boolean;
  summaries: AutoTestSummaries;

  constructor(private adminService: AdminService,
              private titleService: TitleService) {
  }

  ngOnInit() {
    this.titleService.setTitle('Auto Tests', 'Management');

    this.loading = true;
    this.adminService.getAutoTestSummaries().pipe(
      finalize(() => this.loading = false)
    ).subscribe(
      summaries => this.summaries = summaries,
      error => this.error = error.error
    )
  }

}
