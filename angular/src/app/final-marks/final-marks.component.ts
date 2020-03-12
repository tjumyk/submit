import {Component, OnInit} from '@angular/core';
import {ErrorMessage, FinalMarks, Task, User} from "../models";
import {finalize} from "rxjs/operators";
import {AccountService} from "../account.service";
import {AdminService, SetFinalMarksRequest} from "../admin.service";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {TermService} from "../term.service";
import {NgForm} from "@angular/forms";


@Component({
  selector: 'app-final-marks',
  templateUrl: './final-marks.component.html',
  styleUrls: ['./final-marks.component.less']
})
export class FinalMarksComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  isAdmin: boolean;

  loadingStudents: boolean;
  loadingMarks: boolean;
  students: User[];
  studentMap: { [uid: number]: User };
  marks: { [uid: number]: FinalMarks };

  showEditModal: boolean;
  editForm: SetFinalMarksRequest = new SetFinalMarksRequest();
  editError: ErrorMessage;
  submittingEdit: boolean;

  releasing: boolean;

  constructor(private accountService: AccountService,
              private taskService: TaskService,
              private route: ActivatedRoute,
              private termService: TermService,
              private adminService: AdminService) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.parent.paramMap.get('task_id'));

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingStudents = true;
            this.termService.getStudents(task.term_id).pipe(
              finalize(() => this.loadingStudents = false)
            ).subscribe(
              students => {
                this.students = students;
                this.studentMap = {};
                for (let s of students) {
                  this.studentMap[s.id] = s;
                }

                this.loadingMarks = true;
                this.taskService.getFinalMarks(this.taskId).pipe(
                  finalize(() => this.loadingMarks = false)
                ).subscribe(
                  marks => {
                    for (let m of marks) {
                      let student = this.studentMap[m.user_id];
                      if (student) {
                        student['_marks'] = m
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
        let student = this.studentMap[marks.user_id];
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
      },
      error => this.error = error.error
    )
  }
}
