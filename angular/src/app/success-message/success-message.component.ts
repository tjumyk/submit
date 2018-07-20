import {Component, Input, OnInit} from '@angular/core';
import {SuccessMessage} from "../models";

@Component({
  selector: 'app-success-message',
  templateUrl: './success-message.component.html',
  styleUrls: ['./success-message.component.less']
})
export class SuccessMessageComponent implements OnInit {
  private _success: SuccessMessage;
  history: SuccessMessage[] = [];

  @Input() set success(value: SuccessMessage){
    this._success = value;
    if(value != null && value != undefined)
      this.history.push(value)
  };

  get success(): SuccessMessage{
    return this._success;
  }

  constructor() {
  }

  ngOnInit() {
  }

  deleteMessage(index){
    this.history.splice(index, 1);
  }

}
