import {Component, OnDestroy, OnInit} from '@angular/core';
import {NgForm} from "@angular/forms";
import {debounceTime, finalize} from "rxjs/operators";
import {ErrorMessage, Team, User, Task, UserTeamAssociation} from "../models";
import {NewTeamForm, TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {TeamService} from "../team.service";
import {ActivatedRoute, Router} from "@angular/router";
import {Subject} from "rxjs";
import * as moment from "moment";

@Component({
  selector: 'app-join-or-create-team',
  templateUrl: './join-or-create-team.component.html',
  styleUrls: ['./join-or-create-team.component.less']
})
export class JoinOrCreateTeamComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  user: User;

  teamJoinCloseIn: string;
  teamJoinClosed: boolean;
  timeTrackerHandler: number;

  teamAssociation: UserTeamAssociation;
  loadingTeamAssociation: boolean;

  teams: Team[];
  loadingTeams: boolean;

  newTeamForm: NewTeamForm = new NewTeamForm();
  creatingTeam: boolean;

  teamSearchKey = new Subject<string>();
  currentTeamSearchKey: string;
  listedTeams: Team[];

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

    this.teamSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      key => {
        this.currentTeamSearchKey = key;
        this.updateList();
      },
      error => this.error = error.error
    );

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
      if (!task.team_join_close_time) {
        this.teamJoinCloseIn = undefined;
        this.teamJoinClosed = false
      } else {
        const m_join_close = moment(task.team_join_close_time);
        const m_now = moment();
        this.teamJoinClosed = m_join_close.isSameOrBefore(m_now);
        if(this.teamJoinClosed){
          this.teamJoinCloseIn = undefined;
        }else{
          this.teamJoinCloseIn = m_join_close.from(m_now);
        }
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
      this.loadingTeams = true;
      this.taskService.getTeams(this.taskId).pipe(
        finalize(() => this.loadingTeams = false)
      ).subscribe(
        teams => {
          this.teams = teams;
          this.updateList();
        },
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
      error => {
        this.error = error.error;
        window.scroll(0, 0); // simple way to let the user see the error message if the team list is too long
      }
    )
  }

  updateList() {
    let listed: Team[];
    if (this.currentTeamSearchKey) {
      const searchKeyLower = this.currentTeamSearchKey.toLowerCase();
      listed = this.teams.filter((team) => {
        if (team.name.toLowerCase().indexOf(searchKeyLower) >= 0)
          return true;
        if (team.id.toString().indexOf(searchKeyLower) >= 0)
          return true;
        if (team.creator.name.toLowerCase().indexOf(searchKeyLower) >= 0)
          return true;
        if (team.creator.nickname && team.creator.nickname.toLowerCase().indexOf(searchKeyLower) >= 0)
          return true;
        if (team.slogan && team.slogan.toLowerCase().indexOf(searchKeyLower) >= 0)
          return true;
        return false;
      })
    } else {
      listed = this.teams.slice(); // make a copy
    }

    listed.sort((a, b) => {
      if (a.is_finalised && !b.is_finalised)
        return 1;
      if (b.is_finalised && !a.is_finalised)
        return -1;
      return a.id - b.id
    });
    this.listedTeams = listed;
  }

}
