import {Component, OnDestroy, OnInit} from '@angular/core';
import {AutoTest, ErrorMessage, Submission, Task, Team, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TeamService} from "../team.service";
import {TaskService} from "../task.service";
import {AdminService} from "../admin.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-team-submission-details',
  templateUrl: './team-submission-details.component.html',
  styleUrls: ['./team-submission-details.component.less']
})
export class TeamSubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  user: User;
  isAdmin: boolean = false;

  taskId: number;
  task: Task;
  teamId: number;
  team: Team;
  loadingTeam: boolean;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  autoTestsTrackerHandler: number;
  autoTests: AutoTest[];
  getStatusColor: (string) => string;
  selectedAutoTestConfigId: number;
  requestingRunAutoTest: boolean;

  printConclusion: (test:AutoTest)=>any;
  renderResultHTML: (test:AutoTest)=>string;

  constructor(
    private taskService: TaskService,
    private teamService: TeamService,
    private submissionService: SubmissionService,
    private accountService: AccountService,
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
    this.getStatusColor = submissionService.getAutoTestStatusColor;
    this.printConclusion = test => submissionService.printConclusion(test);
    this.renderResultHTML = test => submissionService.renderResultHTML(test);
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.teamId = parseInt(this.route.snapshot.paramMap.get('team_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task=>{
            this.task = task;

            this.loadingTeam = true;
            this.teamService.getTeam(this.teamId).pipe(
              finalize(()=>this.loadingTeam=false)
            ).subscribe(
              team=>{
                this.team = team;

                this.loadingSubmission = true;
                this.submissionService.getSubmission(this.submissionId).pipe(
                  finalize(() => this.loadingSubmission = false)
                ).subscribe(
                  submission => this.setupSubmission(submission),
                  error => this.error = error.error
                )
              }
            )
          },
          error=>this.error=error.error
        )
      },
      error=>this.error=error.error
    )
  }

  ngOnDestroy(){
    clearInterval(this.timeTrackerHandler);
    clearInterval(this.autoTestsTrackerHandler);
  }

  private setupSubmission(submission: Submission){
    // skip team Id check as it is complicated

    if(submission.task_id != this.taskId){
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

  deleteAutoTest(test: AutoTest, btn: HTMLElement) {
    if (!confirm(`Really want to delete test ${test.id}?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteAutoTest(this.submissionId, test.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => {
        let index = 0;
        for (let _test of this.autoTests) {  // use id match to avoid async update issue
          if (_test.id == test.id) {
            this.autoTests.splice(index, 1);
            break;
          }
          ++index;
        }
      },
      error => this.error = error.error
    )
  }

}
