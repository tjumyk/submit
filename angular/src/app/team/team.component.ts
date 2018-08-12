import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Team} from "../models";
import {ActivatedRoute} from "@angular/router";
import {TeamService} from "../team.service";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-team',
  templateUrl: './team.component.html',
  styleUrls: ['./team.component.less']
})
export class TeamComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  teamId: number;
  team: Team;
  loadingTeam: boolean;

  constructor(
    private route: ActivatedRoute,
    private teamService: TeamService
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));
    this.teamId = parseInt(this.route.snapshot.paramMap.get('team_id'));

    this.loadingTeam = true;
    this.teamService.getTeam(this.teamId).pipe(
      finalize(() => this.loadingTeam = false)
    ).subscribe(
      team => this.setupTeam(team),
      error => this.error = error.error
    )
  }

  private setupTeam(team: Team){
    if(team.task_id != this.taskId){
      this.error = {msg: 'Team does not belong to this task'};
      return;
    }
    this.team = team;
  }

}
