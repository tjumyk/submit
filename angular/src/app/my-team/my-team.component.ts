import {Component, OnDestroy, OnInit} from '@angular/core';
import {TaskService} from "../task.service";
import {TeamService, UpdateTeamForm} from "../team.service";
import {ErrorMessage, Task, Team, User, UserTeamAssociation} from "../models";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import {AccountService} from "../account.service";
import * as moment from "moment";

@Component({
  selector: 'app-my-team',
  templateUrl: './my-team.component.html',
  styleUrls: ['./my-team.component.less']
})
export class MyTeamComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  taskId: number;
  user: User;
  task: Task;

  beforeOpen: boolean;
  timeTrackerHandler: number;

  teamAssociation: UserTeamAssociation;
  loadingTeamAssociation: boolean;

  team: Team;
  loadingTeam: boolean;
  reloadingTeam: boolean;

  showUpdateTeamForm: boolean;
  updateTeamForm = new UpdateTeamForm();
  updatingTeam: boolean;

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

        let getTask;
        if (this.route.parent.snapshot.url[0].path == 'tasks-preview') {
          getTask = this.taskService.getCachedTaskPreview(this.taskId);
        } else {
          getTask = this.taskService.getCachedTask(this.taskId);
        }
        getTask.subscribe(
          task => this.setupTask(task),
          error => this.error = error.error
        );
      },
      error => this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
  }

  private setupTask(task: Task) {
    this.task = task;

    const timeTracker = () => {
      if (!task.open_time) {
        this.beforeOpen = true
      } else {
        this.beforeOpen = !moment(task.open_time).isSameOrBefore(moment())
      }
    };
    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10000);

    this.loadingTeamAssociation = true;
    this.taskService.getMyTeamAssociation(this.taskId).pipe(
      finalize(() => this.loadingTeamAssociation = false)
    ).subscribe(
      teamAssociation => this.setupTeamAssociation(teamAssociation),
      error => this.error = error.error
    )
  }

  private setupTeamAssociation(teamAssociation: UserTeamAssociation) {
    this.teamAssociation = teamAssociation;

    if (teamAssociation == null) {
      this.navigateToJoinOrCreateTeam();
    } else {
      this.loadingTeam = true;
      this.teamService.getTeam(this.teamAssociation.team_id).pipe(
        finalize(() => this.loadingTeam = false)
      ).subscribe(
        team => this.setupTeam(team),
        error => this.error = error.error
      )
    }
  }

  private reloadTeam() {
    this.reloadingTeam = true;
    this.teamService.getTeam(this.teamAssociation.team_id).pipe(
      finalize(() => this.reloadingTeam = false)
    ).subscribe(
      team => this.setupTeam(team),
      error => this.error = error.error
    )
  }

  private setupTeam(team: Team) {
    this.team = team;

    this.updateTeamForm.slogan = team.slogan;
  }

  updateTeam() {
    this.updatingTeam = true;
    this.teamService.updateTeam(this.team.id, this.updateTeamForm).pipe(
      finalize(() => this.updatingTeam = false)
    ).subscribe(
      team => this.setupTeam(team),
      error => this.error = error.error
    )
  }

  private navigateToJoinOrCreateTeam() {
    this.router.navigate(['join-or-create'], {relativeTo: this.route, replaceUrl: true})
  }

  cancelJoin(btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.teamService.cancelJoinApplication(this.team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.navigateToJoinOrCreateTeam(),
      error => this.error = error.error
    )
  }

  leaveTeam(btn: HTMLElement) {
    if (!confirm('Really want to leave this team?'))
      return;

    btn.classList.add('loading', 'disabled');
    this.teamService.leaveTeam(this.team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.navigateToJoinOrCreateTeam(),
      error => this.error = error.error
    )
  }

  acceptJoin(applicant: User, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.teamService.acceptJoinApplication(this.team.id, applicant.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.reloadTeam(),
      error => this.error = error.error
    )
  }

  rejectJoin(applicant: User, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.teamService.rejectJoinApplication(this.team.id, applicant.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.reloadTeam(),
      error => this.error = error.error
    )
  }

  kickOut(user: User, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.teamService.kickOut(this.team.id, user.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.reloadTeam(),
      error => this.error = error.error
    )
  }

  finaliseTeam(btn: HTMLElement) {
    if (!confirm("After you finalise the team, the member list will be locked and you won't be able to dismiss the team. Continue?"))
      return;

    btn.classList.add('loading', 'disabled');
    this.teamService.finaliseTeam(this.team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.reloadTeam(),
      error => this.error = error.error
    )
  }

  dismissTeam(btn: HTMLElement) {
    if (!confirm('Really want to dismiss this team?'))
      return;

    btn.classList.add('loading', 'disabled');
    this.teamService.dismissTeam(this.team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.navigateToJoinOrCreateTeam(),
      error => this.error = error.error
    )
  }

  hasPendingRequests(): boolean {
    for (let ass of this.team.user_associations) {
      if (!ass.is_creator_agreed || !ass.is_user_agreed)
        return true;
    }
    return false;
  }

}
