import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, SubmissionStatus, Task, Team} from "../models";
import {AccountService} from "../account.service";
import {AutoTestConclusionsMap, LastAutoTestsMap, TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import {TeamService} from "../team.service";

@Component({
  selector: 'app-team-submission-list',
  templateUrl: './team-submission-list.component.html',
  styleUrls: ['./team-submission-list.component.less']
})
export class TeamSubmissionListComponent implements OnInit {

  error: ErrorMessage;

  taskId: number;
  task: Task;
  teamId: number;
  team: Team;
  status: SubmissionStatus;
  submissions: Submission[];
  loadingTeam: boolean;
  loadingStatus: boolean;
  loadingSubmissions: boolean;
  lastAutoTests: LastAutoTestsMap;
  loadingLastAutoTests: boolean;
  loadingAutoTestConclusions: boolean;
  autoTestConclusions : AutoTestConclusionsMap;

  constructor(
    private accountService: AccountService,
    private teamService: TeamService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.teamId = parseInt(this.route.snapshot.paramMap.get('team_id'));

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingTeam = true;
        this.teamService.getTeam(this.teamId).pipe(
          finalize(() => this.loadingTeam = false)
        ).subscribe(
          team => {
            this.team = team;

            this.loadingStatus = true;
            this.taskService.getTeamSubmissionStatus(this.taskId, this.teamId).pipe(
              finalize(() => this.loadingStatus = false)
            ).subscribe(
              status => {
                this.status = status;

                this.loadingSubmissions = true;
                this.taskService.getTeamSubmissions(this.taskId, this.teamId).pipe(
                  finalize(() => this.loadingSubmissions = false)
                ).subscribe(
                  submissions => {
                    this.submissions = submissions;

                    if(submissions.length == 0 || task.auto_test_configs.length == 0)
                      return;

                    this.loadingLastAutoTests = true;
                    this.taskService.getTeamSubmissionLastAutoTests(this.taskId, this.teamId).pipe(
                      finalize(()=>this.loadingLastAutoTests=false)
                    ).subscribe(
                      tests=>{
                        this.lastAutoTests = tests;

                        this.loadingAutoTestConclusions = true;
                        this.taskService.getTeamSubmissionAutoTestConclusions(this.taskId, this.teamId).pipe(
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
              }
            )
          }
        )
      },
      error => this.error = error.error
    );
  }

}
