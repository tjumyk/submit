import {Component, OnDestroy, OnInit} from '@angular/core';
import {MessageService} from "../message.service";
import {finalize} from "rxjs/operators";
import {ErrorMessage, Message, Term} from "../models";
import * as moment from "moment";
import {Observable} from "rxjs";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-messages',
  templateUrl: './messages.component.html',
  styleUrls: ['./messages.component.less']
})
export class MessagesComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  loadingMessages: boolean;
  messages: Message[];

  termId: number;
  term: Term;
  refreshingMessages: boolean;
  messageRefreshHandler: number;

  timeTrackerHandler: number;

  constructor(private messageService: MessageService,
              private termService: TermService,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.termId = parseInt(this.route.parent.snapshot.paramMap.get('term_id'));
    this.termService.getCachedTerm(this.termId).subscribe(
      term => {
        this.term = term;

        this.loadingMessages = true;
        this.termService.getMessages(this.termId).pipe(
          finalize(() => this.loadingMessages = false)
        ).subscribe(
          msgs => {
            this.setupMessages(msgs);
            this.termService.unreadMessagesCountTrigger();
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
    clearInterval(this.messageRefreshHandler);
  }

  setupMessages(messages: Message[]) {
    this.messages = messages;

    const timeTracker = () => {
      for (let msg of messages) {
        msg['_created_from_now'] = msg.created_at ? moment(msg.created_at).fromNow() : null;
      }
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10000);

    const messageRefresher = () => {
      if(!this.termService.enableMessageRefresh)
        return;

      let request: Observable<Message[]>;
      if (this.messages.length > 0)
        request = this.termService.getMessagesAfterId(this.termId, this.messages[0].id);
      else
        request = this.termService.getMessages(this.termId);

      this.refreshingMessages = true;
      request.pipe(
        finalize(() => this.refreshingMessages = false)
      ).subscribe(
        msgs => {
          this.messages.unshift(...msgs);
          timeTracker(); // update time info
        },
        error => {
          this.error = error.error;
          clearInterval(this.messageRefreshHandler);
        }
      )
    };

    this.messageRefreshHandler = setInterval(messageRefresher, this.termService.messageRefreshPeriod);
  }

  markAllRead(btn: HTMLElement){
    btn.classList.add('disabled', 'loading');
    this.termService.markAllMessagesRead(this.termId).pipe(
      finalize(()=>btn.classList.remove('disabled', 'loading'))
    ).subscribe(
      ()=>{
        for(let msg of this.messages){
          msg.is_read = true
        }
        this.termService.unreadMessagesCountTrigger();
      },
      error=>this.error = error.error
    )
  }

}
