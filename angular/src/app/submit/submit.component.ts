import {Component, OnInit} from '@angular/core';
import {ErrorMessage, FileRequirement, Task, Term, User} from "../models";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.less']
})
export class SubmitComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  user: User;
  termId: number;
  term: Term;
  accessRoles: Set<string>;

  submitting: boolean;
  files: { [key: number]: File } = {};

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private taskService: TaskService,
    private route: ActivatedRoute,
    private router: Router
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;

        this.termId = parseInt(this.route.snapshot.parent.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;
            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));
            this.taskService.getCachedTask(this.taskId).subscribe(
              task => this.setupTask(task),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        );
      },
      error => this.error = error.error
    );
  }

  private setupTask(task: Task) {
    this.task = task;

    for (let req of task.file_requirements) {
      const dotPos = req.name.lastIndexOf('.');
      if (dotPos > 0) {
        req['_extension'] = req.name.substring(dotPos)
      }
    }
  }

  updateFile(req: FileRequirement, fileList: FileList) {
    this.files[req.id] = fileList.length ? fileList.item(0) : null;
    this.verifyFile(req);
  }

  private verifyFile(req: FileRequirement) {
    let hasError = false;
    const errors = {};

    const file = this.files[req.id];
    if (!file) {
      if (!req.is_optional) {
        errors['required'] = true;
        hasError = true;
      }
    } else {
      const ext = req['_extension'];
      if (ext) {
        const dotPos = file.name.lastIndexOf('.');
        if (dotPos > 0) {
          const fileExt = file.name.substring(dotPos);
          if (fileExt != ext) {
            errors['extension'] = true;
            hasError = true;
          }
        } else {
          errors['extension'] = true;
          hasError = true;
        }
      }

      if (req.size_limit != null && file.size > req.size_limit) {
        errors['size'] = true;
        hasError = true;
      }
    }

    if (hasError) {
      req['_form_errors'] = errors;
      return errors;
    } else {
      req['_form_errors'] = null;
      return null;
    }
  }

  submit() {
    let hasError = false;
    for (let req of this.task.file_requirements) {
      if (this.verifyFile(req)) {
        hasError = true;
      }
    }
    if (hasError)
      return;

    this.submitting = true;
    this.taskService.addSubmission(this.taskId, this.files).pipe(
      finalize(() => this.submitting = false)
    ).subscribe(
      submission => this.router.navigate([`../my-submissions/${submission.id}`], {relativeTo: this.route}),
      error => this.error = error.error
    )
  }

}
