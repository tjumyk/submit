import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Team, Term, User} from "../models";
import {TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import {AdminService} from "../admin.service";
import {TermService} from "../term.service";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-teams',
  templateUrl: './teams.component.html',
  styleUrls: ['./teams.component.less']
})
export class TeamsComponent implements OnInit {
  error: ErrorMessage;

  user: User;
  isAdmin: boolean = false;
  termId: number;
  term: Term;
  taskId: number;
  teams: Team[];
  teamFreeUsers: User[];
  totalUsersInTeams: number;
  loadingTeams: boolean;
  loadingTeamFreeUsers: boolean;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private termService: TermService,
    private adminService: AdminService,
    private router: Router,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.termId = parseInt(this.route.parent.parent.snapshot.paramMap.get('term_id'));
    this.taskId = parseInt(this.route.parent.snapshot.paramMap.get('task_id'));

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;

            this.loadingTeams = true;
            this.taskService.getTeams(this.taskId).pipe(
              finalize(() => this.loadingTeams = false)
            ).subscribe(
              teams => {
                this.teams = teams;

                this.totalUsersInTeams = 0;
                for (let team of teams) {
                  this.totalUsersInTeams += team.total_user_associations
                }

                this.loadingTeamFreeUsers = true;
                this.taskService.getTeamFreeUsers(this.taskId).pipe(
                  finalize(() => this.loadingTeamFreeUsers = false)
                ).subscribe(
                  users => this.teamFreeUsers = users,
                  error => this.error = error.error
                )
              },
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  deleteTeam(team: Team, index: number, btn: HTMLElement) {
    if (!confirm(`Really want to delete team "${team.name}"?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteTeam(team.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.teams.splice(index, 1),
      error => this.error = error.error
    )
  }

  goToTeamUser(userKey: string, btn: HTMLElement, inputDiv: HTMLElement){
    let uid = parseInt(userKey);
    let query = null;
    if(isNaN(uid))
      query = this.taskService.getTeamAssociationByUserName(this.taskId, userKey);
    else
      query = this.taskService.getTeamAssociation(this.taskId, uid);

    btn.classList.add('loading', 'disabled');
    inputDiv.classList.add('disabled');
    query.pipe(
      finalize(()=>{
        btn.classList.remove('loading', 'disabled');
        inputDiv.classList.remove('disabled');
      })
    ).subscribe(
      ass=>{
        if(ass){
          this.router.navigate([`${ass.team_id}`], {relativeTo: this.route})
        }else{
          this.error = {msg:'User is not in any team'}
        }
      },
      error=>this.error = error.error
    )

  }

  bindEnter(event: KeyboardEvent, btn: HTMLElement) {
    if (event.keyCode == 13) {// Enter key
      btn.click()
    }
  }

}
