import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Task, Term, User} from "../models";
import {TermService} from "../term.service";
import {AccountService} from "../account.service";
import {debounceTime, finalize} from "rxjs/operators";
import {ActivatedRoute} from "@angular/router";
import {makeSortField, Pagination} from "../table-util";
import {Subject} from "rxjs";
import {TitleService} from "../title.service";
import {TaskService} from "../task.service";

@Component({
  selector: 'app-term-final-marks',
  templateUrl: './term-final-marks.component.html',
  styleUrls: ['./term-final-marks.component.less']
})
export class TermFinalMarksComponent implements OnInit {
  error: ErrorMessage;

  termId: number;
  term: Term;

  user: User;
  isAdmin: boolean;

  loadingTasks: boolean;
  tasks: Task[];
  categories = TaskService.categories;

  loadingUsers: boolean;
  userPages: Pagination<User>;
  userMap: { [uid: number]: User };
  loadingMarks: boolean;

  userSearchKey = new Subject<string>();
  sortField: (field: string, th: HTMLElement) => any;

  constructor(private accountService: AccountService,
              private termService: TermService,
              private titleService: TitleService,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.userSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.userPages.search(key),
      error => this.error = error.error
    );

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.termId = parseInt(this.route.snapshot.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;
            this.titleService.setTitle('Final Marks', `${term.year}S${term.semester}`, term.course.code);

            this.loadingTasks = true;
            this.termService.getTasks(this.termId).pipe(
              finalize(() => this.loadingTasks = false)
            ).subscribe(
              tasks => {
                this.tasks = tasks;

                this.loadingUsers = true;
                this.termService.getStudents(this.termId).pipe(
                  finalize(() => this.loadingUsers = false)
                ).subscribe(
                  users => {
                    this.userPages = new Pagination<User>(users, 500);
                    this.userPages.setSearchMatcher((item, key) => {
                      const keyLower = key.toLowerCase();
                      if (item.name.toLowerCase().indexOf(keyLower) >= 0)
                        return true;
                      if (item.id.toString().indexOf(keyLower) >= 0)
                        return true;
                      if (item.nickname && item.nickname.toLowerCase().indexOf(keyLower) >= 0)
                        return true;
                      return false;
                    });
                    this.sortField = makeSortField(this.userPages);

                    this.userMap = {};
                    for (let u of users) {
                      u['_marks'] = {};
                      this.userMap[u.id] = u;
                    }

                    this.loadingMarks = true;
                    this.termService.getFinalMarks(this.termId).pipe(
                      finalize(() => this.loadingMarks = false)
                    ).subscribe(
                      marks => {
                        for (let m of marks) {
                          let _u = this.userMap[m.user_id];
                          if (_u) {
                            _u['_marks'][m.task_id] = m
                          }
                        }
                      },
                      error => this.error = error.error
                    )
                  },
                  error => this.error = error.error
                )
              },
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        );
      },
      error => this.error = error.error
    );
  }
}
