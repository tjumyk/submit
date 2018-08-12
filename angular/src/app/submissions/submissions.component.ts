import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Task, Team, TeamSubmissionSummary, UserSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-submissions',
  templateUrl: './submissions.component.html',
  styleUrls: ['./submissions.component.less']
})
export class SubmissionsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  userSummaries: UserSubmissionSummary[];
  teamSummaries: TeamSubmissionSummary[];
  loadingSummaries: boolean;

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

        this.loadingSummaries = true;
        this.taskService.getUserSubmissionSummaries(this.taskId).pipe(
          finalize(() => this.loadingSummaries = false)
        ).subscribe(
          summaries => this.userSummaries = summaries,
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    );

  }
}
