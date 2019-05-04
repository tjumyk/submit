import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {finalize} from "rxjs/operators";
import {AutoTestConfig, ErrorMessage, Task, Team, User} from "../models";
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
  requestingRunAutoTest: boolean;

  @Output() error: EventEmitter<ErrorMessage> = new EventEmitter();

  constructor(
    private accountService: AccountService,
    private adminService: AdminService) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.isAdmin = AccountService.isAdmin(user);
      },
      error => this.error.emit(error.error)
    )
  }

  runAutoTest() {
    let config = this.activeConfig;  // make a local copy
    if (config == null)
      return;

    let needPrompt = true;
    let target_header = "all the submissions";
    if (this.lastSubmissionsOnly)
      target_header = "all the last submissions";
    let target = `${target_header} in ${this.task.title}`;
    let api = this.adminService.runAutoTests(config.id, null, null, this.lastSubmissionsOnly);

    if (this.task.is_team_task) {
      if (this.team) {
        target = `${target_header} from team "${this.team.name}" (ID=${this.team.id}) in ${this.task.title}`;
        api = this.adminService.runAutoTests(config.id, null, this.team.id, this.lastSubmissionsOnly);
      }
    } else {
      if (this.user) {
        target = `${target_header} from user "${this.user.name}" (ID=${this.user.id}) in ${this.task.title}`;
        api = this.adminService.runAutoTests(config.id, this.user.id, null, this.lastSubmissionsOnly);
      }
    }

    if (needPrompt && !confirm(`Really want to run auto test "${config.name}" (ID=${config.id}) for ${target}?`))
      return;

    this.requestingRunAutoTest = true;
    api.pipe(
      finalize(() => this.requestingRunAutoTest = false)
    ).subscribe(
      test => {
        alert(`Started auto test "${config.name}" (ID=${config.id}) for ${test.length} submissions`)
      },
      error => this.error.emit(error.error)
    )
  }

}
