import { Component, OnInit } from '@angular/core';
import {TitleService} from "../title.service";
import {ErrorMessage, User} from "../models";
import {AccountService} from "../account.service";

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.less']
})
export class AdminComponent implements OnInit {

  user: User;
  error: ErrorMessage;

  constructor(
    private accountService: AccountService,
    private titleService: TitleService
  ) { }

  ngOnInit() {
    this.titleService.setTitle('Management');

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
      },
      error => this.error = error.error
    );
  }

}
