import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task} from "../models";
import {LatePenalty, TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";

@Component({
  selector: 'app-my-submissions',
  templateUrl: './my-submissions.component.html',
  styleUrls: ['./my-submissions.component.less']
})
export class MySubmissionsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  submissions: Submission[];
  loadingSubmissions: boolean;
  status: SubmissionStatus;
  loadingStatus: boolean;
  attemptOffset: number;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingStatus = true;
        this.taskService.getMySubmissionStatus(this.taskId).pipe(
          finalize(() => this.loadingStatus = false)
        ).subscribe(
          status => {
            this.status = status;

            if (this.task.submission_history_limit != null) {
              this.attemptOffset = Math.max(0, this.status.attempts - this.task.submission_history_limit)
            } else {
              this.attemptOffset = 0;
            }

            this.loadingSubmissions = true;
            this.taskService.getMySubmissions(this.taskId).pipe(
              finalize(() => this.loadingSubmissions = false)
            ).subscribe(
              submissions => this.setupSubmissions(submissions),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      }
    )
  }

  private setupSubmissions(submissions) {
    this.submissions = submissions;

    const penalty = LatePenalty.parse(this.task.late_penalty);
    const dueMoment = moment(this.task.due_time);
    if (this.status.special_consideration && this.status.special_consideration.due_time_extension) {
      dueMoment.add(this.status.special_consideration.due_time_extension, 'hour');
    }
    for (let sub of submissions) {
      const submitMoment = moment(sub.created_at);
      if (submitMoment.isAfter(dueMoment)) {
        const lateDays = Math.ceil(submitMoment.diff(dueMoment, 'day', true));
        sub['_lateDays'] = lateDays;
        if (penalty) {
          sub['_latePenalty'] = penalty.getPenalty(lateDays);
        }
      }
    }
  }
}
