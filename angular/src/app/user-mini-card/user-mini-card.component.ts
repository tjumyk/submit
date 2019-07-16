import {Component, Input, OnInit} from '@angular/core';
import {User} from "../models";

@Component({
  selector: 'app-user-mini-card',
  templateUrl: './user-mini-card.component.html',
  styleUrls: ['./user-mini-card.component.less']
})
export class UserMiniCardComponent implements OnInit {
  @Input()
  user: User;

  @Input()
  enablePopup: boolean = false;

  @Input()
  enableAdmin: boolean = false;

  constructor() {
  }

  ngOnInit() {
  }
}
