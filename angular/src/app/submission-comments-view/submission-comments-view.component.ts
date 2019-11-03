import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {ErrorMessage, Submission, Task, SubmissionComment, User} from "../models";
import {SubmissionService} from "../submission.service";
import {finalize} from "rxjs/operators";
import * as moment from "moment";
import {AccountService} from "../account.service";
import {NgForm} from "@angular/forms";

@Component({
  selector: 'app-submission-comments-view',
  templateUrl: './submission-comments-view.component.html',
  styleUrls: ['./submission-comments-view.component.less']
})
export class SubmissionCommentsViewComponent implements OnInit, OnDestroy {
  @Input()
  task: Task;
  @Input()
  submission: Submission;
  @Input()
  apiBase: string;
  @Input()
  isAdminOrTutor: boolean = false;

  @Output()
  error: EventEmitter<ErrorMessage> = new EventEmitter();

  user: User;
  isAdmin: boolean;
  isTaskClosed: boolean;

  loadingComments: boolean;
  comments: SubmissionComment[];
  timeTrackerHandler: number;

  addingComment: boolean;
  editorContent: string;

  constructor(private accountService: AccountService,
              private submissionService: SubmissionService) {
  }

  ngOnInit() {
    this.checkTaskCloseTime();
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.loadingComments = true;
        this.submissionService.getComments(this.submission.id, this.apiBase).pipe(
          finalize(() => this.loadingComments = false)
        ).subscribe(
          comments => {
            this.comments = comments;

            this.setupTimeTracker()
          },
          error => this.error.emit(error.error)
        )
      },
      error => this.error.emit(error.error)
    )
  }

  ngOnDestroy(): void {
    clearInterval(this.timeTrackerHandler);
  }

  private setupTimeTracker() {
    const timeTracker = () => {
      for (let comment of this.comments) {
        this.updateTimeFields(comment)
      }
      this.checkTaskCloseTime();
    };
    timeTracker();
    this.timeTrackerHandler = setInterval(timeTracker, 10 * 1000);
  }

  private checkTaskCloseTime(){
    this.isTaskClosed = this.task.close_time && moment().isAfter(moment(this.task.close_time));
  }

  private updateTimeFields(comment: SubmissionComment) {
    comment['_created_at_from_now'] = moment(comment.created_at).fromNow();
    comment['_modified_at_from_now'] = moment(comment.modified_at).fromNow();
  }

  addComment(f: NgForm) {
    if (f.invalid)
      return;

    this.addingComment = true;
    this.submissionService.addComment(this.submission.id, this.editorContent, this.apiBase).pipe(
      finalize(() => this.addingComment = false)
    ).subscribe(
      comment => {
        this.comments.push(comment);
        this.updateTimeFields(comment);
      },
      error=>this.error.emit(error.error)
    )
  }

  editComment(comment: SubmissionComment){
    comment['_editor_content'] = comment.content;
    comment['_editing'] = true;
  }

  cancelEditComment(comment: SubmissionComment){
    comment['_editing'] = false;
  }

  updateComment(f: NgForm, comment:SubmissionComment) {
    if (f.invalid)
      return;

    comment['_updating'] = true;
    this.submissionService.updateComment(this.submission.id, comment.id, comment['_editor_content'], this.apiBase).pipe(
      finalize(() => {
        comment['_updating'] = false;
        comment['_editing'] = false;
        comment['_editor_content'] = undefined;
      })
    ).subscribe(
      _comment => {
        comment.content = _comment.content;
        comment.modified_at = _comment.modified_at;

        this.updateTimeFields(comment);
      },
      error=>this.error.emit(error.error)
    )
  }

  removeComment(comment: SubmissionComment, btn: HTMLElement, index: number) {
    let excerpt = comment.content.substr(0, 32);
    if(excerpt.length < comment.content.length)
      excerpt += '...';
    if (!confirm(`Really want to delete comment "${excerpt}"?\n\nThe E-mails and messages that contain this comment will not be deleted.`))
      return;

    btn.classList.add('disabled', 'loading');
    this.submissionService.removeComment(this.submission.id, comment.id, this.apiBase).pipe(
      finalize(() => btn.classList.remove('disabled', 'loading'))
    ).subscribe(
      () => {
        this.comments.splice(index, 1);
      },
      error => this.error.emit(error.error)
    )
  }

}
