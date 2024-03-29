import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task} from "../models";
import {AccountService} from "../account.service";
import {AutoTestConclusionsMap, LastAutoTestsMap, TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

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
  lastAutoTests: LastAutoTestsMap;
  loadingLastAutoTests: boolean;
  loadingAutoTestConclusions: boolean;
  autoTestConclusions : AutoTestConclusionsMap;

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

            this.loadingSubmissions = true;
            this.taskService.getMyTeamSubmissions(this.taskId).pipe(
              finalize(() => this.loadingSubmissions = false)
            ).subscribe(
              submissions => {
                this.submissions = submissions;

                if(submissions.length == 0 || task.auto_test_configs.length == 0)
                  return;

                this.loadingLastAutoTests = true;
                this.taskService.getMyTeamSubmissionLastAutoTests(this.taskId).pipe(
                  finalize(()=>this.loadingLastAutoTests=false)
                ).subscribe(
                  tests=>{
                    this.lastAutoTests = tests;

                    this.loadingAutoTestConclusions = true;
                    this.taskService.getMyTeamSubmissionAutoTestConclusions(this.taskId).pipe(
                      finalize(()=>this.loadingAutoTestConclusions = false)
                    ).subscribe(
                      conclusions => this.autoTestConclusions = conclusions,
                      error=>this.error = error.error
                    )
                  },
                  error=>this.error = error.error
                )
              },
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      }
    )
  }
}
