import { Component, OnInit } from '@angular/core';
import {ErrorMessage, MessageChannel} from "../models";
import {finalize} from "rxjs/operators";
import {MessageService} from "../message.service";
import {Location} from "@angular/common";

@Component({
  selector: 'app-email-subscriptions',
  templateUrl: './email-subscriptions.component.html',
  styleUrls: ['./email-subscriptions.component.less']
})
export class EmailSubscriptionsComponent implements OnInit {
  error: ErrorMessage;

  loadingChannels: boolean;
  channels: MessageChannel[];

  constructor(
    private messageService: MessageService,
    private location: Location
  ) { }

  ngOnInit() {
    this.loadingChannels = true;
    this.messageService.getChannels().pipe(
      finalize(() => this.loadingChannels = false)
    ).subscribe(
      channels => {
        this.channels = channels
      },
      error => this.error = error.error
    )
  }

  setChannelSubscription(channel: MessageChannel, element: HTMLElement) {
    element.classList.add('disabled');
    const inputElement = element.children[0];
    inputElement.setAttribute('disabled', 'disabled');

    const clearDisabled = ()=>{
      element.classList.remove('disabled');
      inputElement.removeAttribute('disabled');
    };

    if (channel.is_subscribed) {
      this.messageService.subscribeChannel(channel.id).pipe(
        finalize(clearDisabled)
      ).subscribe(
        () => {
        },
        error => this.error = error.error
      )
    } else {
      this.messageService.unsubscribeChannel(channel.id).pipe(
        finalize(clearDisabled)
      ).subscribe(
        () => {
        },
        error => this.error = error.error
      )
    }
  }

  navigateBack(){
    this.location.back()
  }
}
