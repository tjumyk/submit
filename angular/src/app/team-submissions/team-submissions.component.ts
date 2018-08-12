import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Task, TeamSubmissionSummary, UserSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-team-submissions',
  templateUrl: './team-submissions.component.html',
  styleUrls: ['./team-submissions.component.less']
})
export class TeamSubmissionsComponent implements OnInit {

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
        this.taskService.getTeamSubmissionSummaries(this.taskId).pipe(
          finalize(() => this.loadingSummaries = false)
        ).subscribe(
          summaries => this.teamSummaries = summaries,
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    );

  }

}
