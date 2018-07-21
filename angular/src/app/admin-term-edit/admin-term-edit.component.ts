import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, Term, User} from "../models";
import {AdminService} from "../admin.service";
import {ActivatedRoute} from "@angular/router";
import {debounceTime, distinctUntilChanged, finalize, switchMap} from "rxjs/operators";
import {Subject} from "rxjs/internal/Subject";
import {of} from "rxjs/internal/observable/of";

@Component({
  selector: 'app-admin-term-edit',
  templateUrl: './admin-term-edit.component.html',
  styleUrls: ['./admin-term-edit.component.less']
})
export class AdminTermEditComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;
  loadingTerm: boolean;
  termId: number;
  term: Term;

  private searchGroupNames = new Subject<string>();
  groupSearchResults: Group[];
  private searchUserNames = new Subject<string>();
  userSearchResults: Group[];

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.termId = parseInt(this.route.snapshot.paramMap.get('team_id'));

    this.loadTerm();
    this.setupSearch();
  }

  private loadTerm() {
    this.loadingTerm = true;
    this.adminService.getTerm(this.termId).pipe(
      finalize(() => this.loadingTerm = false)
    ).subscribe(
      term => this.term = term,
      error => this.error = error.error
    )
  }

  private setupSearch() {
    this.searchUserNames.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((name: string) => {
        if (!name)
          return of(null);
        return this.adminService.searchUsersByName(name, 10)
      })
    ).subscribe(
      (results) => this.userSearchResults = results,
      (error) => this.error = error.error
    );

    this.searchGroupNames.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((name: string) => {
        if (!name)
          return of(null);
        return this.adminService.searchGroupsByName(name, 10)
      })
    ).subscribe(
      (results) => this.groupSearchResults = results,
      (error) => this.error = error.error
    );
  }

  searchUser(name: string) {
    this.searchUserNames.next(name);
  }

  searchGroup(name: string) {
    this.searchGroupNames.next(name);
  }

  userAlreadyHasAssociation(user: User, role: string) {
    for (let asso of this.term.user_associations) {
      if (asso.user_id == user.id && asso.role == role)
        return true;
    }
    return false;
  }

  groupAlreadyHasAssociation(group: Group, role: string) {
    for (let asso of this.term.group_associations) {
      if (asso.group_id == group.id && asso.role == role)
        return true;
    }
    return false;
  }

  addUserAssociation(user: User, role: string, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.adminService.addUserTermAssociation(user, this.term, role).pipe(
      finalize((() => btn.classList.remove('loading', 'disabled')))
    ).subscribe(
      () => {
        const asso = {user_id: user.id, user: user, term_id: this.term.id, term: this.term, role: role};
        this.term.user_associations.push(asso)
      },
      error => this.error = error.error
    )
  }

  addGroupAssociation(group: Group, role: string, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.adminService.addGroupTermAssociation(group, this.term, role).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => {
        const asso = {group_id: group.id, group: group, term_id: this.term.id, term: this.term, role: role};
        this.term.group_associations.push(asso)
      },
      error => this.error = error.error
    )
  }

  removeUserAssociation(user: User, role: string, index: number, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.adminService.removeUserTermAssociation(user, this.term, role).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.term.user_associations.splice(index, 1),
      error => this.error = error.error
    )
  }

  removeGroupAssociation(group: Group, role: string, index: number, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.adminService.removeGroupTermAssociation(group, this.term, role).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.term.group_associations.splice(index, 1),
      error => this.error = error.error
    )
  }

}
