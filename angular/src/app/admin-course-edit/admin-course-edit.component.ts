import {Component, OnInit} from '@angular/core';
import {Course, ErrorMessage, SuccessMessage} from "../models";
import {ActivatedRoute} from "@angular/router";
import {AdminService, NewTermForm} from "../admin.service";
import {finalize} from "rxjs/operators";
import {UploadFilters, UploadValidator} from "../upload-util";
import {NgForm} from "@angular/forms";
import * as moment from "moment";

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

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.course_id = parseInt(this.route.snapshot.paramMap.get('course_id'));

    const now = moment();
    this.newTermForm.year = now.year();
    const month = now.month();
    if(month < 5)
      this.newTermForm.semester = '1';
    else if(month < 9)
      this.newTermForm.semester = '2';
    else if(month <12)
      this.newTermForm.semester = '3';
    else
      this.newTermForm.semester = 'summer';

    this.loadCourse();
  }

  loadCourse() {
    this.loadingCourse = true;
    this.adminService.getCourse(this.course_id).pipe(
      finalize(() => this.loadingCourse = false)
    ).subscribe(
      course => this.course = course,
      error => this.error = error.error
    )
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
    if(!confirm(`Really want to delete term ${term.year}S${term.semester}? This is not recoverable!`))
      return

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

}
