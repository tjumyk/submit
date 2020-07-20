import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {finalize} from "rxjs/operators";
import {AutoTestConfig, ErrorMessage, SuccessMessage, Task, Team, User} from "../models";
import {AccountService} from "../account.service";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-run-auto-test-card',
  templateUrl: './run-auto-test-card.component.html',
  styleUrls: ['./run-auto-test-card.component.less']
})
export class RunAutoTestCardComponent implements OnInit {
  @Input() task: Task;
  @Input() user: User;
  @Input() team: Team;

  isAdmin: boolean;

  activeConfig: AutoTestConfig;
  lastSubmissionsOnly: boolean;
  skipSuccessful: boolean;
  requestingRunAutoTest: boolean;

  showModal: boolean;
  modalError: ErrorMessage;
  modelSuccess: SuccessMessage;

  constructor(
    private accountService: AccountService,
    private adminService: AdminService) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.isAdmin = AccountService.isAdmin(user);
      },
      error => this.modalError = error.error
    )
  }

  runAutoTest() {
    let config = this.activeConfig;  // make a local copy
    if (config == null)
      return;

    let api = this.adminService.runAutoTests(config.id, null, null,
      this.lastSubmissionsOnly, this.skipSuccessful);

    if (this.task.is_team_task) {
      if (this.team) {
        api = this.adminService.runAutoTests(config.id, null, this.team.id,
          this.lastSubmissionsOnly, this.skipSuccessful);
      }
    } else {
      if (this.user) {
        api = this.adminService.runAutoTests(config.id, this.user.id, null,
          this.lastSubmissionsOnly, this.skipSuccessful);
      }
    }

    this.requestingRunAutoTest = true;
    api.pipe(
      finalize(() => this.requestingRunAutoTest = false)
    ).subscribe(
      test => {
        this.modelSuccess = {msg: `Started auto test "${config.name}" on ${test.length} submissions`}
      },
      error => this.modalError = error.error
    )
  }

}
