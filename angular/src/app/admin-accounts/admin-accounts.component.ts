import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, User} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-admin-accounts',
  templateUrl: './admin-accounts.component.html',
  styleUrls: ['./admin-accounts.component.less']
})
export class AdminAccountsComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;
  loadingUsers: boolean;
  loadingGroups: boolean;
  users: User[];
  groups: Group[];

  syncingUsers: boolean;
  syncingGroups: boolean;

  constructor(
    private adminService: AdminService
  ) {
  }

  ngOnInit() {
    this.loadUsers();
    this.loadGroups();
  }

  private loadGroups() {
    this.loadingGroups = true;
    this.adminService.getGroups().pipe(
      finalize(() => this.loadingGroups = false)
    ).subscribe(
      groups => this.groups = groups,
      error => this.error = error.error
    )
  }

  private loadUsers() {
    this.loadingUsers = true;
    this.adminService.getUsers().pipe(
      finalize(() => this.loadingUsers = false)
    ).subscribe(
      users => this.users = users,
      error => this.error = error.error
    );
  }

  syncUsers() {
    this.syncingUsers = true;
    this.adminService.syncUsers().pipe(
      finalize(() => this.syncingUsers = false)
    ).subscribe(
      () => this.loadUsers(),
      (error) => this.error = error.error
    )
  }

  syncGroups() {
    this.syncingGroups = true;
    this.adminService.syncGroups().pipe(
      finalize(() => this.syncingGroups = false)
    ).subscribe(
      () => this.loadGroups(),
      (error) => this.error = error.error
    )
  }

}
