import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Message} from "../models";
import {MessageService} from "../message.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import * as moment from "moment";

@Component({
  selector: 'app-message-detail',
  templateUrl: './message-detail.component.html',
  styleUrls: ['./message-detail.component.less']
})
export class MessageDetailComponent implements OnInit, OnDestroy {
  error: ErrorMessage;

  loadingMessage: boolean;
  mid: number;
  message: Message;
  markingRead: boolean;

  timeTrackerHandler: number;

  constructor(
    private messageService: MessageService,
    private route: ActivatedRoute,
    private router: Router
  ) {
  }

  ngOnInit() {
    this.mid = parseInt(this.route.snapshot.paramMap.get('msg_id'));

    this.loadingMessage = true;
    this.messageService.getById(this.mid).pipe(
      finalize(() => this.loadingMessage = false)
    ).subscribe(
      msg => {
        this.setupMessage(msg);
      },
      error => this.error = error.error
    )
  }

  ngOnDestroy() {
    clearInterval(this.timeTrackerHandler);
  }

  setupMessage(message: Message) {
    this.message = message;

    const timeTracker = () => {
      message['_created_from_now'] = message.created_at ? moment(message.created_at).fromNow() : null;
    };

    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10000);

    if(!message.is_read){
      this.markingRead = true;
      this.messageService.markRead(message.id).pipe(
        finalize(()=>this.markingRead =false)
      ).subscribe(
        ()=>{
          this.message.is_read = true
        },
        error=>this.error = error.error
      )
    }
  }

  handleRouterLinks(event: MouseEvent){
    const target = event.target as Element;
    if(target.tagName == 'A' && target.classList.contains('router') && target.classList.contains('link')){ // is a router link
      this.router.navigateByUrl(target.getAttribute('href'));
      // event.stopPropagation(); TODO is this required?
      return false;
    }
  }

}
