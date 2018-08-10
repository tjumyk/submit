import {Component, OnInit} from '@angular/core';
import {AdminService, NewCourseForm} from "../admin.service";
import {ErrorMessage} from "../models";
import {NgForm} from "@angular/forms";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-admin-course-new',
  templateUrl: './admin-course-new.component.html',
  styleUrls: ['./admin-course-new.component.less']
})
export class AdminCourseNewComponent implements OnInit {
  error: ErrorMessage;
  addingCourse: boolean;
  form: NewCourseForm = new NewCourseForm();

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.form.is_new_tutor_group = true;
  }

  ngOnInit() {
  }

  newCourse(f: NgForm) {
    if (f.invalid)
      return;

    this.addingCourse = true;
    this.adminService.addCourse(this.form).pipe(
      finalize(() => this.addingCourse = false)
    ).subscribe(
      (course) => this.router.navigate([`../courses/${course.id}`], {relativeTo: this.route}),
      (error) => this.error = error.error
    )
  }

  autoFillForm(){
    if(this.form.code){
      let shortCode = this.form.code.substr(-4, 4);
      this.form.tutor_group_name = `${shortCode}_tutor`
    }else{
      this.form.tutor_group_name = ''
    }
  }

}
