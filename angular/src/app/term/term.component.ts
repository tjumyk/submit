import {Component, OnDestroy, OnInit} from '@angular/core';
import {ErrorMessage, Term, User} from "../models";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import {TitleService} from "../title.service";
import {MetaService} from "../meta.service";

@Component({
  selector: 'app-term',
  templateUrl: './term.component.html',
  styleUrls: ['./term.component.less']
})
export class TermComponent implements OnInit, OnDestroy {
  initError: ErrorMessage;
  messageCheckError: ErrorMessage;

  termId: number;
  term: Term;
  loadingTerm: boolean;

  user: User;
  isAdmin: boolean;
  accessRoles: Set<string>;

  checking_messages: boolean;
  message_check_handler: number;
  messages_unread_count: number;

  showMobileMenu: boolean;

  clockDeltaMaxRange = 5000; // ms
  clockDeltaMaxOffset = 60000; // ms

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private route: ActivatedRoute,
    private titleService: TitleService,
    private metaService: MetaService
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user=>{
        this.user=user;
        this.isAdmin = AccountService.isAdmin(user);

        this.termId = parseInt(this.route.snapshot.paramMap.get('term_id'));
        this.loadingTerm = true;
        this.termService.getTerm(this.termId).pipe(
          finalize(() => this.loadingTerm = false)
        ).subscribe(
          term => {
            this.term = term;
            this.titleService.setTitle(`${term.year}S${term.semester}`, term.course.code);

            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.setupMessageCheck();
            this.setupClockCheck();
          },
          error => this.initError = error.error
        )
      },
      error => this.initError = error.error
    );
  }

  ngOnDestroy(){
    clearInterval(this.message_check_handler);
    this.termService.unreadMessagesCountTrigger = () => undefined;
  }

  resetMobileMenu() {
    this.showMobileMenu = false
  }

  setupMessageCheck(){
    const doMessageCheck = ()=>{
      this.checking_messages = true;
      this.termService.getUnreadMessagesCount(this.termId).pipe(
        finalize(() => this.checking_messages = false)
      ).subscribe(
        count => this.messages_unread_count = count,
        error => {
          this.messageCheckError = error.error;
          clearInterval(this.message_check_handler)
        }
      )
    };

    const messageChecker = ()=>{
      if(!this.termService.enableMessageRefresh)
        return;
      doMessageCheck()
    };

    this.termService.unreadMessagesCountTrigger = () => doMessageCheck();
    this.message_check_handler = setInterval(messageChecker, this.termService.messageRefreshPeriod);
    doMessageCheck();
  }

  private setupClockCheck() {
    let tStart = new Date().getTime();
    this.metaService.getClock().subscribe(
      clock => {
        let tEnd = new Date().getTime();
        let tServer = clock.time * 1000; // second to millisecond
        let deltaLowerBound = tServer - tEnd;
        let deltaUpperBound = tServer - tStart;
        if (Math.abs(deltaUpperBound - deltaLowerBound) <= this.clockDeltaMaxRange) {
          let delta = Math.abs((deltaUpperBound + deltaLowerBound) / 2);
          if (delta > this.clockDeltaMaxOffset) {
            alert('Your system clock is not correct. Some functions might be impacted.\n\nPlease calibrate your system clock and then restart your browser.')
          }
        }
      }
    )
  }
}
