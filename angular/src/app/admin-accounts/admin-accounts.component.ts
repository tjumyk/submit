import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, User} from "../models";
import {AdminService} from "../admin.service";
import {debounceTime, finalize} from "rxjs/operators";
import {makeSortField, Pagination} from "../table-util";
import {Subject} from "rxjs";
import {TitleService} from "../title.service";

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
  userPages: Pagination<User>;
  userSearchKey = new Subject<string>();
  groups: Group[];

  syncingUsers: boolean;
  syncingGroups: boolean;

  sortField: (field: string, th: HTMLElement)=>any;

  constructor(
    private adminService: AdminService,
    private titleService: TitleService
  ) {
  }

  ngOnInit() {
    this.titleService.setTitle('Accounts', 'Management');

    this.userSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.userPages.search(key),
      error => this.error = error.error
    );

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
      users => {
        this.userPages = new Pagination<User>(users, 10);
        this.sortField = makeSortField(this.userPages);
        this.userPages.setSearchMatcher((user: User, key: string) => {
          const keyLower = key.toLowerCase();
          if (user.name.toLowerCase().indexOf(keyLower) >= 0)
            return true;
          if (user.id.toString().indexOf(keyLower) >= 0)
            return true;
          if (user.nickname && user.nickname.toLowerCase().indexOf(keyLower) >= 0)
            return true;
          if (user.email && user.email.toLowerCase().indexOf(keyLower) >= 0)
            return true;
          return false;
        });
      },
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

  syncUser(user: User, btn: HTMLElement) {
    btn.classList.add('disabled', 'loading');
    this.adminService.syncUser(user.id).pipe(
      finalize(() => {
        btn.classList.remove('disabled', 'loading');
      })
    ).subscribe(
      (_user) => {
        user.email = _user.email;
        user.avatar = _user.avatar;
        user.nickname = _user.nickname;
        user.groups = _user.groups;  // I am lazy
      },
      (error) => this.error = error.error
    )
  }

  syncGroup(group: Group, btn: HTMLElement) {
    btn.classList.add('disabled', 'loading');
    this.adminService.syncGroup(group.id).pipe(
      finalize(() => {
        btn.classList.remove('disabled', 'loading');
      })
    ).subscribe(
      (_group) => {
        group.description = _group.description;

        // Also update the groups of the currently loaded users in a lazy way (linear scan).
        // This api may also add new users but they are ignored here because
        //   (1) the api may only return user ids rather than full user objects for efficiency.
        //   (2) also, it brings more cost to append new table rows and redo the filtering or sorting.
        // A page refresh is okay.
        const user_ids = new Set();
        for (let uid of _group['user_ids']) {
          user_ids.add(uid);
        }
        for (let user of this.userPages.items) {
          let groupIndex = -1;
          let i = 0;
          for (let g of user.groups) {
            if (g.id == _group.id) {
              groupIndex = i;
              break;
            }
            ++i;
          }
          if (user_ids.has(user.id)) {
            user_ids.delete(user.id);
            if (groupIndex == -1)
              user.groups.push(group)
          } else {
            if (groupIndex >= 0)
              user.groups.splice(groupIndex, 1)
          }
        }
        if(user_ids.size > 0)
          alert(`${user_ids.size} new users added. You need to refresh the page if you want to see them.`)
      },
      (error) => this.error = error.error
    )
  }

  deleteUser(user: User, btn: HTMLElement) {
    if (!confirm(`Really want to delete user "${user.name}"? Only local alias will be deleted.`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteUser(user.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => {
        let index = 0;
        for (let _user of this.userPages.sourceItems) {
          if (_user.id == user.id) {
            this.userPages.sourceItems.splice(index, 1);
            this.userPages.reload();
            break;
          }
          ++index;
        }
      },
      error => this.error = error.error
    )
  }

  deleteGroup(group: Group, index: number, btn: HTMLElement) {
    if (!confirm(`Really want to delete group "${group.name}"? Only local alias will be deleted.`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteGroup(group.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.groups.splice(index, 1),
      error => this.error = error.error
    )
  }

}
