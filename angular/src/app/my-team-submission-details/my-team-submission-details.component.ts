import {Component, OnDestroy, OnInit} from '@angular/core';
import {AutoTest, ErrorMessage, Submission, SuccessMessage, Task, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-my-team-submission-details',
  templateUrl: './my-team-submission-details.component.html',
  styleUrls: ['./my-team-submission-details.component.less']
})
export class MyTeamSubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;
  success: SuccessMessage;

  user: User;
  taskId: number;
  task: Task;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  autoTestsTrackerHandler: number;
  autoTests: AutoTest[];

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;
        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingSubmission = true;
            this.submissionService.getMyTeamSubmission(this.submissionId).pipe(
              finalize(() => this.loadingSubmission = false)
            ).subscribe(
              submission => this.setupSubmission(submission),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      },
      error=>this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
    clearInterval(this.autoTestsTrackerHandler);
  }

  private setupSubmission(submission: Submission) {
    if (submission.task_id != this.taskId) {
      this.error = {msg: 'submission does not belong to this task'};
      return;
    }

    this.submission = submission;
    if (submission.submitter_id == this.user.id && moment().diff(moment(submission.created_at), 'seconds') < 3)
      this.success = {msg: 'Submitted successfully'};

    const timeTracker = () => {
      this.createdFromNow = moment(submission.created_at).fromNow()
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 30000);

    if (this.task.evaluation_method == 'auto_test') {
      const autoTestsTracker = () => {
        let needRefresh = false;
        if (!this.autoTests) {
          needRefresh = true; // first load
        } else {
          for (let test of this.autoTests) {
            if (!test.final_state) {
              needRefresh = true;
              break;
            }
          }
        }
        if (!needRefresh)
          return; // skip request if all (current) works finished

        this.submissionService.getMyTeamAutoTestAndResults(this.submissionId).subscribe(
          tests => {
            for (let test of tests) {
              for (let config of this.task.auto_test_configs) {
                if (config.id == test.config_id) {
                  test.config = config;
                  break;
                }
              }
            }
            this.autoTests = tests;
          },
          error => {
            this.error = error.error;
            clearInterval(this.autoTestsTrackerHandler);  // stop further requests
          }
        )
      };

      autoTestsTracker();
      this.autoTestsTrackerHandler = setInterval(autoTestsTracker, 5000);
    }
  }

}
