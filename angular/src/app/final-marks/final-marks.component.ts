import {Component, OnInit} from '@angular/core';
import {ErrorMessage, FinalMarks, SuccessMessage, Task, User} from "../models";
import {debounceTime, finalize} from "rxjs/operators";
import {AccountService} from "../account.service";
import {AdminService, SetFinalMarksRequest} from "../admin.service";
import {TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {TermService} from "../term.service";
import {NgForm} from "@angular/forms";
import {makeSortField, Pagination} from "../table-util";
import {Subject} from "rxjs";
import * as moment from "moment";


@Component({
  selector: 'app-final-marks',
  templateUrl: './final-marks.component.html',
  styleUrls: ['./final-marks.component.less']
})
export class FinalMarksComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;

  taskId: number;
  task: Task;
  isAdmin: boolean;

  loadingUsers: boolean;
  loadingMarks: boolean;
  userPages: Pagination<User>;
  userMap: { [uid: number]: User };

  showEditModal: boolean;
  editForm: SetFinalMarksRequest = new SetFinalMarksRequest();
  editError: ErrorMessage;
  submittingEdit: boolean;

  releasing: boolean;

  userSearchKey = new Subject<string>();
  sortField: (field: string, th: HTMLElement) => any;

  constructor(private accountService: AccountService,
              private taskService: TaskService,
              private route: ActivatedRoute,
              private termService: TermService,
              private adminService: AdminService,
              private router: Router) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.parent.paramMap.get('task_id'));

    this.userSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.userPages.search(key),
      error => this.error = error.error
    );

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingUsers = true;
            this.termService.getStudents(task.term_id).pipe(
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
                  this.userMap[u.id] = u;
                }

                this.loadingMarks = true;
                this.taskService.getFinalMarks(this.taskId).pipe(
                  finalize(() => this.loadingMarks = false)
                ).subscribe(
                  marks => {
                    for (let m of marks) {
                      m['_created_at_time'] = moment(m.created_at).unix();
                      m['_modified_at_time'] = moment(m.modified_at).unix();
                      let _u = this.userMap[m.user_id];
                      if (_u) {
                        _u['_marks'] = m
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
    )
  }

  startEdit(user: User, form: NgForm) {
    let marks = user['_marks'];
    if (marks) {
      this.editForm.marks = marks.marks;
      this.editForm.comment = marks.comment;
    } else {
      form.resetForm()
    }
    this.editForm.user_id = user.id;
    this.editError = undefined;
    this.showEditModal = true;
  }

  submitEdit(form: NgForm) {
    if (form.invalid)
      return;

    this.submittingEdit = true;
    this.adminService.setFinalMarks(this.taskId, this.editForm).pipe(
      finalize(() => this.submittingEdit = false)
    ).subscribe(
      marks => {
        let student = this.userMap[marks.user_id];
        if (student)
          student['_marks'] = marks;
        this.showEditModal = false
      },
      error => this.editError = error.error
    )
  }

  release() {
    if (!confirm('Really want to release the final marks?\nYou will not be able to make any changes once they are released.'))
      return;

    this.releasing = true;
    this.adminService.releaseFinalMarks(this.taskId).pipe(
      finalize(() => this.releasing = false)
    ).subscribe(
      () => {
        this.task.is_final_marks_released = true;
        this.success = {msg: 'Final marks have been released successfully'}
      },
      error => this.error = error.error
    )
  }

  goToTeamSubmissions(user: User, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.taskService.getTeamAssociation(this.taskId, user.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ass => {
        if (ass) {
          this.router.navigate(['terms', this.task.term_id, 'tasks', this.taskId, 'team-submissions', ass.team_id])
        } else {
          alert('Team not found')
        }
      },
      error => this.error = error.error
    )
  }
}
