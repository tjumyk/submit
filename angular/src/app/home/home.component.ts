import {Component, OnInit} from '@angular/core';
import {AccountService} from "../account.service";
import {Course, ErrorMessage, Term, User} from "../models";
import {finalize} from "rxjs/operators";
import {CourseService} from "../course.service";
import {ActivatedRoute, Router} from "@angular/router";
import {TitleService} from "../title.service";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.less']
})
export class HomeComponent implements OnInit {
  error: ErrorMessage;
  loadingUser: boolean;
  loadingCourses: boolean;
  user: User;
  isAdmin: boolean;
  courses: Course[];
  courseMap: { [key: number]: Course };
  entries: { [key: number]: Term[] };
  defaultEntries: { [key: number]: Term };

  constructor(
    private accountService: AccountService,
    private courseService: CourseService,
    private route: ActivatedRoute,
    private router: Router,
    private titleService: TitleService
  ) {
  }

  ngOnInit() {
    this.titleService.setTitle();

    this.loadUser();
  }

  private loadUser() {
    this.loadingUser = true;
    this.accountService.getCurrentUser().pipe(
      finalize(() => this.loadingUser = false)
    ).subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);
        this.loadCourses();
      },
      error => this.error = error.error
    )
  }

  private loadCourses() {
    this.loadingCourses = true;
    this.courseService.getCourses().pipe(
      finalize(() => this.loadingCourses = false)
    ).subscribe(
      courses => {
        this.courses = courses;
        this.courseMap = {};
        for (let course of courses)
          this.courseMap[course.id] = course;
        this.setupEntries();
      },
      error => this.error = error.error
    )
  }

  private setupEntries() {
    let entries: { [course_id: number]: { [term_id: number]: Term } } = {};
    for (let course of this.courses) {
      let list_course = false;
      if (this.isAdmin)
        list_course = true;
      else {
        for (let group of this.user.groups) {
          if (group.id == course.tutor_group_id) { // tutor of course
            list_course = true;
            break;
          }
        }
      }

      if (list_course) {
        let course_entries = entries[course.id];
        if (!course_entries) {
          entries[course.id] = course_entries = []
        }
        for (let term of course.terms) {
          course_entries[term.id] = term
        }
      }

      for (let term of course.terms) {
        for (let group of this.user.groups) {
          if (group.id == term.student_group_id) { // student of term
            let course_entries = entries[course.id];
            if (!course_entries) {
              entries[course.id] = course_entries = []
            }
            course_entries[term.id] = term;
            break;
          }
        }
      }
    }

    this.entries = {};
    this.defaultEntries = {};

    let totalTermEntries = 0;
    let lastTermEntry: Term;
    for (let course_id in entries) {
      let terms_dict = entries[course_id];
      let terms = [];
      for (let term_id in terms_dict) {
        terms.push(terms_dict[term_id])
      }
      terms.sort((a: Term, b: Term) => {
        if (a.year != b.year)
          return b.year - a.year;
        if (a.semester != b.semester) {
          let a_sem = parseInt(a.semester) || 0;
          let b_sem = parseInt(b.semester) || 0;
          return b_sem - a_sem
        }
        return b.id - a.id;
      });
      this.entries[course_id] = terms;
      totalTermEntries += terms.length;
      if (terms.length > 0) {
        lastTermEntry = terms[0];
        this.defaultEntries[course_id] = lastTermEntry;
      }
    }

    if (!this.isAdmin && totalTermEntries == 1) {
      this.router.navigate([`terms/${lastTermEntry.id}`], {relativeTo: this.route})
    }
  }

  goDefault(courseId: number) {
    const course = this.courseMap[courseId];
    if (!course) {
      alert(`Invalid course ID: ${courseId}`);
      return;
    }
    const term = this.defaultEntries[courseId];
    if (term) {
      this.router.navigate([`terms/${term.id}`], {relativeTo: this.route})
    } else {
      alert(`Course "${course.code} ${course.name}" has no accessible terms yet`)
    }
  }

}
