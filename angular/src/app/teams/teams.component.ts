import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Team} from "../models";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-teams',
  templateUrl: './teams.component.html',
  styleUrls: ['./teams.component.less']
})
export class TeamsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  teams: Team[];
  loadingTeams: boolean;

  constructor(
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));

    this.loadingTeams = true;
    this.taskService.getTeams(this.taskId).pipe(
      finalize(() => this.loadingTeams = false)
    ).subscribe(
      teams => this.teams = teams,
      error => this.error = error.error
    )
  }

}
