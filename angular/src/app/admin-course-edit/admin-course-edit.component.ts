import {Component, OnInit} from '@angular/core';
import {Course, ErrorMessage, SuccessMessage, Term} from "../models";
import {ActivatedRoute} from "@angular/router";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";
import {UploadFilters, UploadValidator} from "../upload-util";

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
  terms: Term[];

  uploadingIcon: boolean;
  iconValidator: UploadValidator = new UploadValidator(UploadFilters.icon);

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.course_id = parseInt(this.route.snapshot.paramMap.get('course_id'));

    this.loadCourse();
    this.loadTerms();
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

  loadTerms(){

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

}
