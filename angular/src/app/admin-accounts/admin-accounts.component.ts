import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, User} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";
import {Pagination} from "../table-util";

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
  userPages = new Pagination<User>();
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
      users => this.userPages.sourceItems = users,
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

  deleteUser(user:User, btn:HTMLElement){
    if(!confirm(`Really want to delete user "${user.name}"? Only local alias will be deleted.`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteUser(user.id).pipe(
      finalize(()=>btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ()=>{
        let index = 0;
        for(let _user of this.userPages.sourceItems){
          if(_user.id == user.id){
            this.userPages.sourceItems.splice(index, 1);
            this.userPages.reload();
            break;
          }
          ++index;
        }
      },
      error=>this.error=error.error
    )
  }

  deleteGroup(group:Group, index: number, btn:HTMLElement){
    if(!confirm(`Really want to delete group "${group.name}"? Only local alias will be deleted.`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteGroup(group.id).pipe(
      finalize(()=>btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ()=>this.groups.splice(index, 1),
      error=>this.error=error.error
    )
  }

  sortField(field: string, th: HTMLElement) {
    let sibling = th.parentNode.firstChild;
    while (sibling) {
      if (sibling.nodeType == 1 && sibling != th) {
        (sibling as Element).classList.remove('sorted', 'descending', 'ascending');
      }
      sibling = sibling.nextSibling;
    }

    if (!th.classList.contains('sorted')) {
      th.classList.add('sorted', 'ascending');
      th.classList.remove('descending');
      this.userPages.sort(field, false);
    } else {
      if (th.classList.contains('ascending')) {
        th.classList.remove('ascending');
        th.classList.add('descending');
        this.userPages.sort(field, true);
      } else {
        th.classList.remove('sorted', 'descending', 'ascending');
        this.userPages.sort(null);
      }
    }
  }

}
