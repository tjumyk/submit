import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Team} from "../models";
import {SubmissionService} from "../submission.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {TeamService} from "../team.service";

@Component({
  selector: 'app-team-submission-details',
  templateUrl: './team-submission-details.component.html',
  styleUrls: ['./team-submission-details.component.less']
})
export class TeamSubmissionDetailsComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  taskId: number;
  teamId: number;
  team: Team;
  loadingTeam: boolean;
  submissionId: number;
  submission: Submission;
  loadingSubmission: boolean;

  timeTrackerHandler: number;
  createdFromNow: string;

  constructor(
    private teamService: TeamService,
    private submissionService: SubmissionService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.teamId = parseInt(this.route.snapshot.paramMap.get('team_id'));
    this.submissionId = parseInt(this.route.snapshot.paramMap.get('submission_id'));

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
  }

  ngOnDestroy(){
    clearInterval(this.timeTrackerHandler);
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
  }

}
