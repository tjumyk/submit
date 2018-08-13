import {Component, Input, OnInit} from '@angular/core';
import {ErrorMessage} from "../models";

@Component({
  selector: 'app-error-message',
  templateUrl: './error-message.component.html',
  styleUrls: ['./error-message.component.less']
})
export class ErrorMessageComponent implements OnInit {
  private _error: ErrorMessage;
  history: ErrorMessage[] = [];

  @Input() set error(value: ErrorMessage) {
    if(value instanceof ProgressEvent && value.type == 'error'){
      value = {
        msg: 'connection failed'
      }
    }

    this._error = value;
    if(value != null && value != undefined)
      this.history.push(value)
  }

  get error(): ErrorMessage {
    return this._error;
  }

  constructor() {
  }

  ngOnInit() {
  }

  deleteMessage(index){
    this.history.splice(index, 1);
  }

  redirect(url){
    window.location.href=url;
  }

}
