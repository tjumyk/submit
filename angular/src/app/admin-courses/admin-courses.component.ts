import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Course, Term} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";
import {TitleService} from "../title.service";

@Component({
  selector: 'app-admin-courses',
  templateUrl: './admin-courses.component.html',
  styleUrls: ['./admin-courses.component.less']
})
export class AdminCoursesComponent implements OnInit {

  error: ErrorMessage;
  loadingCourses: boolean;
  courses: Course[];

  constructor(
    private adminService: AdminService,
    private titleService: TitleService
  ) { }

  ngOnInit() {
    this.titleService.setTitle('Courses', 'Management');

    this.loadCourses();
  }

  private loadCourses(){
    this.loadingCourses = true;
    this.adminService.getCourses().pipe(
      finalize(()=>this.loadingCourses=false)
    ).subscribe(
      (courses) => this.courses = courses,
      (error)=> this.error = error.error
    )
  }

  deleteCourse(course, index, btn:HTMLElement){
    if(!confirm(`Really want to delete course "${course.code} - ${course.name}"? This is not recoverable!`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteCourse(course.id).pipe(
      finalize(()=>btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ()=>this.courses.splice(index, 1),
      (error)=>this.error=error.error
    )
  }


}
