import {Component, OnDestroy, OnInit} from '@angular/core';
import {AutoTest, ErrorMessage, Submission, Task, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TaskService} from "../task.service";
import {AdminService} from "../admin.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-submission-details',
  templateUrl: './submission-details.component.html',
  styleUrls: ['./submission-details.component.less']
})
export class SubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  user: User;
  isAdmin: boolean = false;

  taskId: number;
  task: Task;
  userId: number;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  autoTestsTrackerHandler: number;
  autoTests: AutoTest[];
  selectedAutoTestConfigId: number;
  requestingRunAutoTest: boolean;

  constructor(
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private accountService: AccountService,
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.userId = parseInt(this.route.snapshot.paramMap.get('user_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingSubmission = true;
            this.submissionService.getSubmission(this.submissionId).pipe(
              finalize(() => this.loadingSubmission = false)
            ).subscribe(
              submission => this.setupSubmission(submission),
              error => this.error = error.error
            )
          },
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
    if (submission.submitter_id != this.userId) {
      this.error = {msg: 'submission does not belong to this user'};
      return;
    }
    if (submission.task_id != this.taskId) {
      this.error = {msg: 'submission does not belong to this task'};
      return;
    }

    this.submission = submission;

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

        this.submissionService.getAutoTestAndResults(this.submissionId).subscribe(
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
            clearInterval(this.autoTestsTrackerHandler);  // stop further requests if error occurs
          }
        )
      };

      autoTestsTracker();
      this.autoTestsTrackerHandler = setInterval(autoTestsTracker, 5000);
    }
  }

  runAutoTest() {
    if(this.selectedAutoTestConfigId == null)
      return;

    this.requestingRunAutoTest = true;
    this.adminService.runAutoTest(this.submissionId, this.selectedAutoTestConfigId).pipe(
      finalize(() => this.requestingRunAutoTest = false)
    ).subscribe(
      test => {
        for(let config of this.task.auto_test_configs){
          if(config.id == test.config_id){
            test.config = config;
            break;
          }
        }
        this.autoTests.push(test);
      },
      error => this.error = error.error
    )
  }

  onAutoTestDeleted(test: AutoTest) {
    let index = 0;
    for (let _test of this.autoTests) {  // use id match to avoid async update issue
      if (_test.id == test.id) {
        this.autoTests.splice(index, 1);
        break;
      }
      ++index;
    }
  }
}
