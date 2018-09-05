import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task, User} from "../models";
import {AccountService} from "../account.service";
import {LatePenalty, TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";

@Component({
  selector: 'app-my-team-submissions',
  templateUrl: './my-team-submissions.component.html',
  styleUrls: ['./my-team-submissions.component.less']
})
export class MyTeamSubmissionsComponent implements OnInit {

  error: ErrorMessage;

  taskId: number;
  task: Task;

  loadingStatus: boolean;
  status: SubmissionStatus;
  submissions: Submission[];
  loadingSubmissions: boolean;
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
        this.taskService.getMyTeamSubmissionStatus(this.taskId).pipe(
          finalize(() => this.loadingStatus = false)
        ).subscribe(
          status => {
            this.status = status;

            if (!status.team_association || !status.team_association.team.is_finalised)
              return;

            if (this.task.submission_history_limit != null) {
              this.attemptOffset = Math.max(0, this.status.attempts - this.task.submission_history_limit)
            } else {
              this.attemptOffset = 0;
            }

            this.loadingSubmissions = true;
            this.taskService.getMyTeamSubmissions(this.taskId).pipe(
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

  private setupSubmissions(submissions: Submission[]) {
    this.submissions = submissions;

    const penalty = LatePenalty.parse(this.task.late_penalty);
    const dueMoment = moment(this.task.due_time);
    if(this.status.special_consideration && this.status.special_consideration.due_time_extension){
      dueMoment.add(this.status.special_consideration.due_time_extension, 'hour');
    }
    for(let sub of submissions){
      const submitMoment = moment(sub.created_at);
      if(submitMoment.isAfter(dueMoment)){
        const lateDays = Math.ceil(submitMoment.diff(dueMoment, 'day', true));
        sub['_lateDays'] = lateDays;
        if(penalty){
          sub['_latePenalty'] = penalty.getPenalty(lateDays);
        }
      }
    }
  }
}
