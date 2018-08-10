import {Component, OnInit} from '@angular/core';
import {Course, ErrorMessage, Group, SuccessMessage} from "../models";
import {ActivatedRoute} from "@angular/router";
import {AdminService, NewTermForm} from "../admin.service";
import {debounceTime, distinctUntilChanged, finalize, switchMap} from "rxjs/operators";
import {UploadFilters, UploadValidator} from "../upload-util";
import {NgForm} from "@angular/forms";
import * as moment from "moment";
import {Subject} from "rxjs/internal/Subject";
import {of} from "rxjs/internal/observable/of";

@Component({
  selector: 'app-admin-course-edit',
  templateUrl: './admin-course-edit.component.html',
  styleUrls: ['./admin-course-edit.component.less']
})
export class AdminCourseEditComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;

  loadingCourse: boolean;
  course_id: number;
  course: Course;

  addingTerm: boolean;
  newTermForm: NewTermForm = new NewTermForm();

  uploadingIcon: boolean;
  iconValidator: UploadValidator = new UploadValidator(UploadFilters.icon);

  searchingGroups: boolean;
  private searchGroupNames = new Subject<string>();
  groupSearchResults: Group[];
  searchingUsers: boolean;
  private searchUserNames = new Subject<string>();
  userSearchResults: Group[];

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
    this.newTermForm.is_new_student_group = true;
  }

  ngOnInit() {
    this.course_id = parseInt(this.route.snapshot.paramMap.get('course_id'));

    const now = moment();
    this.newTermForm.year = now.year();
    const month = now.month();
    if (month < 5)
      this.newTermForm.semester = '1';
    else if (month < 9)
      this.newTermForm.semester = '2';
    else if (month < 12)
      this.newTermForm.semester = '3';
    else
      this.newTermForm.semester = 'summer';

    this.loadCourse();
    this.setupSearch();
  }

  private loadCourse() {
    this.loadingCourse = true;
    this.adminService.getCourse(this.course_id).pipe(
      finalize(() => this.loadingCourse = false)
    ).subscribe(
      course => {
        this.course = course;
        this.autoFillForm();
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
        return this.adminService.searchGroupsByName(name, 10)
      })
    ).subscribe(
      (results) => this.groupSearchResults = results,
      (error) => this.error = error.error
    );
  }

  uploadIcon(input: HTMLInputElement) {
    let files = input.files;
    if (files.length == 0)
      return;

    let file = files.item(0);
    if (!this.iconValidator.check(file)) {
      input.value = '';  // reset
      this.error = this.iconValidator.error;
      return;
    }

    this.uploadingIcon = true;
    this.adminService.updateCourseIcon(this.course_id, file).pipe(
      finalize(() => {
        this.uploadingIcon = false;
        input.value = '';  // reset
      })
    ).subscribe(
      (course) => {
        this.course = course;
        this.success = {msg: 'Uploaded course icon successfully'}
      },
      (error) => this.error = error.error
    )
  }

  addTerm(f: NgForm) {
    if (f.invalid)
      return;

    this.addingTerm = true;
    this.adminService.addTerm(this.course_id, this.newTermForm).pipe(
      finalize(() => this.addingTerm = false)
    ).subscribe(
      term => {
        this.course.terms.push(term);
        this.success = {msg: `Added new term ${term.year}S${term.semester} successfully`}
      },
      error => this.error = error.error
    )
  }

  deleteTerm(term, index, btn: HTMLElement) {
    if (!confirm(`Really want to delete term ${term.year}S${term.semester}? This is not recoverable!`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteTerm(term.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => {
        this.course.terms.splice(index, 1);
        this.success = {msg: `Deleted term ${term.year}S${term.semester} successfully`};
      },
      error => this.error = error.error
    )
  }

  searchUser(name: string) {
    this.searchUserNames.next(name);
  }

  searchGroup(name: string) {
    this.searchGroupNames.next(name);
  }

  autoFillForm(){
    if(this.newTermForm.year && this.newTermForm.semester){
      let shortCode = this.course.code.substr( -4, 4);
      let shortYear = this.newTermForm.year % 100;
      let shortSemester = this.newTermForm.semester[0];
      this.newTermForm.student_group_name = `${shortCode}_${shortYear}s${shortSemester}_student`
    }else{
      this.newTermForm.student_group_name = ''
    }
  }

}
