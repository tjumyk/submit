import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Submission, Task, Team} from "../models";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";
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
  submissions: Submission[];
  loadingSubmissions: boolean;

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

        this.teamService.getTeam(this.teamId).subscribe(
          team => {
            this.team = team;

            this.loadingSubmissions = true;
            this.taskService.getTeamSubmissions(this.taskId, this.teamId).pipe(
              finalize(() => this.loadingSubmissions = false)
            ).subscribe(
              submissions => this.submissions = submissions,
              error => this.error = error.error
            )
          }
        )
      },
      error => this.error = error.error
    );
  }

}
