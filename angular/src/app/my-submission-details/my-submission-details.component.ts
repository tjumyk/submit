import {Component, OnDestroy, OnInit} from '@angular/core';
import {AutoTest, ErrorMessage, Submission, SuccessMessage, Task} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-my-submission-details',
  templateUrl: './my-submission-details.component.html',
  styleUrls: ['./my-submission-details.component.less']
})
export class MySubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;
  success: SuccessMessage;

  taskId: number;
  task: Task;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  autoTestsTrackerHandler: number;
  autoTests: AutoTest[];
  getStatusColor: (string) => string;

  printConclusion: (test:AutoTest)=>any;
  renderResultHTML: (test:AutoTest)=>string;

  constructor(
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
    this.getStatusColor = submissionService.getAutoTestStatusColor;
    this.printConclusion = AdminService.printConclusion;
    this.renderResultHTML = AdminService.renderResultHTML;
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingSubmission = true;
        this.submissionService.getMySubmission(this.submissionId).pipe(
          finalize(() => this.loadingSubmission = false)
        ).subscribe(
          submission => this.setupSubmission(submission),
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
    clearInterval(this.autoTestsTrackerHandler);
  }

  private setupSubmission(submission: Submission) {
    this.submission = submission;

    if (moment().diff(moment(submission.created_at), 'seconds') < 3)
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

        this.submissionService.getMyAutoTestAndResults(this.submissionId).subscribe(
          tests => {
            for(let test of tests){
              for(let config of this.task.auto_test_configs){
                if(config.id == test.config_id){
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
