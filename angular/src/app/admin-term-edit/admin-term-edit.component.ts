import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, Task, Term} from "../models";
import {AdminService, NewTaskForm} from "../admin.service";
import {ActivatedRoute} from "@angular/router";
import {debounceTime, distinctUntilChanged, finalize, switchMap} from "rxjs/operators";
import {Subject} from "rxjs/internal/Subject";
import {of} from "rxjs/internal/observable/of";
import {NgForm} from "@angular/forms";
import {TitleService} from "../title.service";

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
  newTaskForm: NewTaskForm = new NewTaskForm();
  addingNewTask: boolean;

  searchingGroups: boolean;
  private searchGroupNames = new Subject<string>();
  groupSearchResults: Group[];
  searchingUsers: boolean;
  private searchUserNames = new Subject<string>();
  userSearchResults: Group[];

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute,
    private titleService: TitleService
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
      term => {
        this.term = term;
        this.titleService.setTitle(`${term.year}S${term.semester}`, term.course.code, 'Management');
      },
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
        this.searchingUsers = true;
        return this.adminService.searchUsersByName(name, 10).pipe(
          finalize(() => this.searchingUsers = false)
        )
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
        this.searchingGroups = false;
        return this.adminService.searchGroupsByName(name, 10).pipe(
          finalize(() => this.searchingGroups = false)
        )
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

  addTask(f: NgForm) {
    if (f.invalid)
      return;

    this.addingNewTask = true;
    this.adminService.addTask(this.termId, this.newTaskForm).pipe(
      finalize(() => this.addingNewTask = false)
    ).subscribe(
      task => this.term.tasks.push(task),
      error => this.error = error.error
    )
  }

  removeTask(task: Task, index: number, btn: HTMLElement) {
    if(!confirm(`Really want to delete task "${task.title}"?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteTask(task.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.term.tasks.splice(index, 1),
      error => this.error = error.error
    )
  }

  autoFillTaskTitle() {
    if (this.newTaskForm.type) {
      let type = this.newTaskForm.type;
      let count = 0;
      for (let task of this.term.tasks) {
        if (task.type == type)
          ++count;
      }
      type = type[0].toUpperCase() + type.substring(1);
      this.newTaskForm.title = `${type} ${count + 1}`
    } else {
      this.newTaskForm.title = ''
    }
  }
}
