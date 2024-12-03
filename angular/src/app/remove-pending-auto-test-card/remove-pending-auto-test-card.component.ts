import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {finalize} from "rxjs/operators";
import {AutoTestConfig, ErrorMessage, SuccessMessage, Task, Team, User} from "../models";
import {AccountService} from "../account.service";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-remove-pending-auto-test-card',
  templateUrl: './remove-pending-auto-test-card.component.html',
  styleUrls: ['./remove-pending-auto-test-card.component.less']
})
export class RemovePendingAutoTestCardComponent implements OnInit {
  @Input() task: Task;

  isAdmin: boolean;

  activeConfig: AutoTestConfig;
  requesting: boolean;

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

  removePendingAutoTest() {
    let config = this.activeConfig;  // make a local copy
    if (config == null)
      return;

    this.requesting = true;
    this.adminService.removePendingAutoTests(config.id).pipe(
      finalize(() => this.requesting = false)
    ).subscribe(
      result => {
        this.modelSuccess = {msg: `Removed ${result.total} pending auto tests of "${config.name}"`}
      },
      error => this.modalError = error.error
    )
  }

}
