import {Component, Input, OnInit} from '@angular/core';
import {SuccessMessage} from "../models";

@Component({
  selector: 'app-success-message',
  templateUrl: './success-message.component.html',
  styleUrls: ['./success-message.component.less']
})
export class SuccessMessageComponent implements OnInit {
  @Input() success: SuccessMessage;

  constructor() {
  }

  ngOnInit() {
  }

}
