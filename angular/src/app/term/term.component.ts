import {Component, OnInit} from '@angular/core';
import {ErrorMessage, SuccessMessage, Term, User} from "../models";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-term',
  templateUrl: './term.component.html',
  styleUrls: ['./term.component.less']
})
export class TermComponent implements OnInit {
  error: ErrorMessage;

  termId: number;
  term: Term;
  loadingTerm: boolean;

  user: User;
  isAdmin: boolean;

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user=user;
        this.isAdmin = AccountService.isAdmin(user);

        this.termId = parseInt(this.route.snapshot.paramMap.get('term_id'));
        this.loadingTerm = true;
        this.termService.getTerm(this.termId).pipe(
          finalize(() => this.loadingTerm = false)
        ).subscribe(
          term => this.term = term,
          error => this.error = error.error
        )
      },
      error=>this.error=error.error
    );

  }

}
