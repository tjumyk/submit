import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task} from "../models";
import {AutoTestConclusionsMap, LastAutoTestsMap, TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

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
        this.taskService.getMySubmissionStatus(this.taskId).pipe(
          finalize(() => this.loadingStatus = false)
        ).subscribe(
          status => {
            this.status = status;

            this.loadingSubmissions = true;
            this.taskService.getMySubmissions(this.taskId).pipe(
              finalize(() => this.loadingSubmissions = false)
            ).subscribe(
              submissions => {
                this.submissions = submissions;

                if(submissions.length == 0 || task.auto_test_configs.length == 0)
                  return;

                this.loadingLastAutoTests = true;
                this.taskService.getMySubmissionLastAutoTests(this.taskId).pipe(
                  finalize(()=>this.loadingLastAutoTests=false)
                ).subscribe(
                  tests=>{
                    this.lastAutoTests = tests;

                    this.loadingAutoTestConclusions = true;
                    this.taskService.getMySubmissionAutoTestConclusions(this.taskId).pipe(
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
