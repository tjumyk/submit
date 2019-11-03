import {Component, OnInit} from '@angular/core';
import {TaskService} from "../task.service";
import {ErrorMessage, Submission, SubmissionCommentSummary, Task, User} from "../models";
import {ActivatedRoute, Router} from "@angular/router";
import {debounceTime, finalize} from "rxjs/operators";
import {AccountService} from "../account.service";
import {makeSortField, Pagination} from "../table-util";
import {Subject} from "rxjs";
import * as moment from "moment";

@Component({
  selector: 'app-comments',
  templateUrl: './comments.component.html',
  styleUrls: ['./comments.component.less']
})
export class CommentsComponent implements OnInit {
  error: ErrorMessage;

  user: User;
  isAdmin: boolean;

  taskId: number;
  task: Task;

  loadingSummaries: boolean;
  summaries: SubmissionCommentSummary[];
  summaryPages: Pagination<SubmissionCommentSummary>;

  excerptThreshold: number = 32;

  totalComments: number;
  searchKey = new Subject<string>();
  sortField: (field: string, th: HTMLElement) => any;

  constructor(private accountService: AccountService,
              private taskService: TaskService,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));

    this.searchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.summaryPages.search(key),
      error => this.error = error.error
    );

    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.taskService.getCachedTask(this.taskId).subscribe(
          task => {
            this.task = task;

            this.loadingSummaries = true;
            this.taskService.getSubmissionCommentSummaries(this.taskId).pipe(
              finalize(() => this.loadingSummaries = false)
            ).subscribe(
              summaries => {
                this.summaries = summaries;

                this.totalComments = 0;
                for (let item of summaries) {
                  this.totalComments += item.total_comments;
                  item['_last_comment_time'] = moment(item.last_comment.modified_at).unix();
                }
                this.summaryPages = new Pagination(summaries, 500);
                this.summaryPages.setSearchMatcher((item, key)=>{
                  const keyLower = key.toLowerCase();
                  if(item.submission.id.toString().indexOf(keyLower) >= 0)
                    return true;
                  const users = [item.submission.submitter];
                  if(item.last_comment.author)
                    users.push(item.last_comment.author);
                  for(let user of users){
                    if(user.id.toString().indexOf(keyLower) >= 0)
                      return true;
                    if(user.name.toLowerCase().indexOf(keyLower) >= 0)
                      return true;
                    if(user.nickname && user.nickname.toLowerCase().indexOf(keyLower) >= 0)
                      return true;
                  }
                  if(item.last_comment.content.toLowerCase().indexOf(keyLower) >= 0)
                    return true;
                  return false;
                });
                this.sortField = makeSortField(this.summaryPages);
              },
              error => this.error = error.error
            )
          }
        )
      }
    )
  }

  gotoTeamSubmission(submission: Submission, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.taskService.getTeamAssociation(submission.task_id, submission.submitter_id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ass => {
        if (ass == null) {
          this.error = {msg: 'team association not found'};
          return
        }
        this.router.navigate([`team-submissions/${ass.team_id}/${submission.id}`], {relativeTo: this.route.parent})
      },
      error => this.error = error.error
    )
  }

}
