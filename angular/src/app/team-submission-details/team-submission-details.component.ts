import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Task, Team, User} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import {TeamService} from "../team.service";
import {TaskService} from "../task.service";
import {AdminService} from "../admin.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-team-submission-details',
  templateUrl: './team-submission-details.component.html',
  styleUrls: ['./team-submission-details.component.less']
})
export class TeamSubmissionDetailsComponent implements OnInit {
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

  constructor(
    private taskService: TaskService,
    private teamService: TeamService,
    private submissionService: SubmissionService,
    private accountService: AccountService,
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.teamId = parseInt(this.route.snapshot.paramMap.get('team_id'));

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

                this.route.paramMap.subscribe(
                  paramMap=>{
                    // reset
                    this.submissionId = undefined;
                    this.submission = undefined;

                    // load
                    this.submissionId = parseInt(paramMap.get('submission_id'));
                    this.loadingSubmission = true;
                    this.submissionService.getSubmission(this.submissionId).pipe(
                      finalize(() => this.loadingSubmission = false)
                    ).subscribe(
                      submission => this.setupSubmission(submission),
                      error => this.error = error.error
                    )
                  }
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

  private setupSubmission(submission: Submission){
    // skip team Id check as it is complicated

    if(submission.task_id != this.taskId){
      this.error = {msg: 'submission does not belong to this task'};
      return;
    }

    this.submission = submission;
  }

}
