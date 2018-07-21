import {Component, OnInit} from '@angular/core';
import {AccountService} from "../account.service";
import {ErrorMessage, User} from "../models";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.less']
})
export class HomeComponent implements OnInit {
  error: ErrorMessage;
  loadingUser: boolean;
  user: User;
  isAdmin: boolean;

  constructor(
    private accountService: AccountService
  ) {
  }

  ngOnInit() {
    this.loadingUser = true;
    this.accountService.getCurrentUser().pipe(
      finalize(() => this.loadingUser = false)
    ).subscribe(
      user => {
        this.user = user;
        for (let group of user.groups) {
          if (group.name == 'admin')
            this.isAdmin = true;
        }
      },
      error => this.error = error.error
    )
  }

}
