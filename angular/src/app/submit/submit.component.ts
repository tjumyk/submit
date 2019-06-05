import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, FileRequirement, Submission, SubmissionStatus, Task, Term, User} from "../models";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {LatePenalty} from '../late-penalty';
import {HttpEventType} from "@angular/common/http";

export class AttemptEntry {
  attempted: boolean;
  special: boolean;
}

@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.less']
})
export class SubmitComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  user: User;
  termId: number;
  term: Term;
  accessRoles: Set<string>;

  status: SubmissionStatus;
  loadingStatus: boolean;

  isReadyToSubmit: boolean;
  isClosed: boolean;
  attemptEntries: AttemptEntry[];

  countDownHours: number;
  countDownMinutes: number;
  countDownSeconds: number;

  lateDays: number;
  latePenalty: number;

  timeTrackerHandler: number;

  submitting: boolean;
  submitProgress: number;
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

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
  }

  private setupTask(task: Task) {
    this.task = task;

    for (let req of task.file_requirements) {
      const dotPos = req.name.lastIndexOf('.');
      if (dotPos > 0) {
        req['_extension'] = req.name.substring(dotPos)
      }
    }

    if (task.is_team_task) {
      this.loadingStatus = true;
      this.taskService.getMyTeamSubmissionStatus(this.taskId).pipe(
        finalize(() => this.loadingStatus = false)
      ).subscribe(
        status => this.setupStatus(status),
        error => this.error = error.error
      )
    } else {
      this.loadingStatus = true;
      this.taskService.getMySubmissionStatus(this.taskId).pipe(
        finalize(() => this.loadingStatus = false)
      ).subscribe(
        status => this.setupStatus(status),
        error => this.error = error.error
      )
    }
  }

  private setupStatus(status: SubmissionStatus) {
    this.status = status;

    this.attemptEntries = this.buildAttemptEntries();

    const countDownThreshold = 72 * 60 * 60; // only show the count-down if less than 72 hours left
    const penalty = LatePenalty.parse(this.task.late_penalty);

    const timeTracker = () => {
      this.checkTimeAndReadyToSubmit();

      if (this.task.due_time) {
        let due_moment = moment(this.task.due_time);
        if (this.status.special_consideration && this.status.special_consideration.due_time_extension)
          due_moment = due_moment.add(this.status.special_consideration.due_time_extension, 'h');

        let remain = due_moment.diff(moment(), 's');
        if (remain < 0) {
          this.countDownHours = null;
          this.countDownMinutes = null;
          this.countDownSeconds = null;

          this.lateDays = Math.ceil(-remain / 60 / 60 / 24);
          if (penalty) {
            this.latePenalty = penalty.getPenalty(this.lateDays);
          }
        } else {
          this.lateDays = null;
          this.latePenalty = null;

          if (remain < countDownThreshold) {
            this.countDownSeconds = remain % 60;
            remain = Math.floor(remain / 60);
            this.countDownMinutes = remain % 60;
            remain = Math.floor(remain / 60);
            this.countDownHours = remain;
          } else {
            this.countDownHours = null;
            this.countDownMinutes = null;
            this.countDownSeconds = null;
          }
        }
      }
    };
    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 1000);
  }

  private checkTimeAndReadyToSubmit() {
    // check time
    this.isClosed = this.task.close_time && moment().isAfter(moment(this.task.close_time));
    if (this.isClosed) {
      this.isReadyToSubmit = false;
      return;
    }

    // check team
    if (this.task.is_team_task && (!this.status.team_association || !this.status.team_association.team.is_finalised)) {
      this.isReadyToSubmit = false;
      return;
    }

    // check attempt limit
    if (this.task.submission_attempt_limit != null) {
      let attemptLimit = this.task.submission_attempt_limit;
      if (this.status.special_consideration && this.status.special_consideration.submission_attempt_limit_extension)
        attemptLimit += this.status.special_consideration.submission_attempt_limit_extension;
      this.isReadyToSubmit = this.status.attempts < attemptLimit;
    } else {
      this.isReadyToSubmit = true;
    }
  }

  private buildAttemptEntries(): AttemptEntry[] {
    if (this.task.submission_attempt_limit != null && this.status.attempts != null) {
      let attemptLimit = this.task.submission_attempt_limit;
      if (this.status.special_consideration && this.status.special_consideration.submission_attempt_limit_extension)
        attemptLimit += this.status.special_consideration.submission_attempt_limit_extension;

      const entries: AttemptEntry[] = [];
      for (let i = 0; i < attemptLimit; ++i) {
        entries.push({
          attempted: i < this.status.attempts,
          special: i >= this.task.submission_attempt_limit
        })
      }
      return entries
    } else {
      return null;
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
    this.submitProgress = 0;
    this.taskService.addSubmission(this.taskId, this.files).pipe(
      finalize(() => this.submitting = false)
    ).subscribe(
      event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            this.submitProgress = Math.round(100 * event.loaded / event.total);
            break;
          case HttpEventType.Response:
            const submission = event.body as Submission;
            let redirect;
            if (this.task.is_team_task)
              redirect = `../my-team-submissions/${submission.id}`;
            else
              redirect = `../my-submissions/${submission.id}`;
            this.router.navigate([redirect], {relativeTo: this.route})
        }
      },
      error => this.error = error.error
    )
  }

}
