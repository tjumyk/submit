import {Component, Input, OnInit} from '@angular/core';
import {ErrorMessage} from "../models";

@Component({
  selector: 'app-error-message',
  templateUrl: './error-message.component.html',
  styleUrls: ['./error-message.component.less']
})
export class ErrorMessageComponent implements OnInit {
  @Input() error: ErrorMessage;

  constructor() {
  }

  ngOnInit() {
  }

}
