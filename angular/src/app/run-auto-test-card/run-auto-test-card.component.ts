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
    let target = `all the submissions for ${this.task.title}`;
    let api = this.adminService.runAutoTests(config.id);

    if (this.task.is_team_task) {
      if (this.team) {
        target = `all the submissions from team "${this.team.name}" (ID=${this.team.id}) in ${this.task.title}`;
        api = this.adminService.runAutoTests(config.id, null, this.team.id);
      }
    } else {
      if (this.user) {
        target = `all the submissions from user "${this.user.name}" (ID=${this.user.id}) in ${this.task.title}`;
        api = this.adminService.runAutoTests(config.id, this.user.id, null);
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
