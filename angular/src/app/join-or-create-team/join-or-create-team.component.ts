import {Component, OnInit} from '@angular/core';
import {NgForm} from "@angular/forms";
import {finalize} from "rxjs/operators";
import {ErrorMessage, Team, User, UserTeamAssociation} from "../models";
import {NewTeamForm, TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {TeamService} from "../team.service";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-join-or-create-team',
  templateUrl: './join-or-create-team.component.html',
  styleUrls: ['./join-or-create-team.component.less']
})
export class JoinOrCreateTeamComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  user: User;

  teamAssociation: UserTeamAssociation;
  loadingTeamAssociation: boolean;

  teams: Team[];
  loadingTeams: boolean;

  newTeamForm: NewTeamForm = new NewTeamForm();
  creatingTeam: boolean;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private teamService: TeamService,
    private route: ActivatedRoute,
    private router: Router
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;

        this.loadingTeamAssociation = true;
        this.taskService.getMyTeamAssociation(this.taskId).pipe(
          finalize(() => this.loadingTeamAssociation = false)
        ).subscribe(
          teamAssociation => this.setupTeamAssociation(teamAssociation),
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  private setupTeamAssociation(teamAssociation: UserTeamAssociation) {
    this.teamAssociation = teamAssociation;

    if (teamAssociation == null) {
      this.loadingTeams = true;
      this.taskService.getTeams(this.taskId).pipe(
        finalize(() => this.loadingTeams = false)
      ).subscribe(
        teams => this.teams = teams,
        error => this.error = error.error
      )
    } else {
      this.navigateToMyTeam();
    }
  }

  private navigateToMyTeam() {
    this.router.navigate(['..'], {relativeTo: this.route, replaceUrl: true})
  }

  createTeam(f: NgForm) {
    if (f.invalid)
      return;

    this.creatingTeam = true;
    this.taskService.addTeam(this.taskId, this.newTeamForm).pipe(
      finalize(() => this.creatingTeam = false)
    ).subscribe(
      team => this.navigateToMyTeam(),
      error => this.error = error.error
    )
  }

  applyJoin(team: Team, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.teamService.applyJoin(team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.navigateToMyTeam(),
      error => this.error = error.error
    )
  }

}
