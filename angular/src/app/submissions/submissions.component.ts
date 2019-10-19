import {Component, OnInit} from '@angular/core';
import {DailySubmissionSummary, ErrorMessage, Task, UserSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {AllAutoTestConclusionsMap, TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {debounceTime, finalize} from "rxjs/operators";
import {SubmissionService} from "../submission.service";
import {makeSortField, Pagination} from "../table-util";
import * as moment from "moment";
import {Subject} from "rxjs";

@Component({
  selector: 'app-submissions',
  templateUrl: './submissions.component.html',
  styleUrls: ['./submissions.component.less']
})
export class SubmissionsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  userSummaries: UserSubmissionSummary[];
  userSummaryPages: Pagination<UserSubmissionSummary>;
  totalSubmissions: number;
  loadingSummaries: boolean;
  loadingAutoTestConclusions: boolean;
  autoTestConclusions: AllAutoTestConclusionsMap;

  loadingDailySummaries: boolean;
  dailySummaries: DailySubmissionSummary[];

  userSearchKey = new Subject<string>();
  sortField: (field: string, th: HTMLElement) => any;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private submissionService: SubmissionService,
    private router: Router,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));

    this.userSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.userSummaryPages.search(key),
      error => this.error = error.error
    );

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingSummaries = true;
        this.taskService.getUserSubmissionSummaries(this.taskId).pipe(
          finalize(() => this.loadingSummaries = false)
        ).subscribe(
          summaries => {
            this.userSummaries = summaries;

            this.totalSubmissions = 0;
            for (let item of summaries) {
              this.totalSubmissions += item.total_submissions;
              item['_first_submit_time'] = moment(item.first_submit_time).unix();
              item['_last_submit_time'] = moment(item.last_submit_time).unix()
            }
            this.userSummaryPages = new Pagination(summaries, 500);
            this.userSummaryPages.setSearchMatcher((item, key) => {
              const keyLower = key.toLowerCase();
              if (item.user.name.toLowerCase().indexOf(keyLower) >= 0)
                return true;
              if (item.user.id.toString().indexOf(keyLower) >= 0)
                return true;
              if (item.user.nickname && item.user.nickname.toLowerCase().indexOf(keyLower) >= 0)
                return true;
              return false;
            });
            this.sortField = makeSortField(this.userSummaryPages);

            if (this.totalSubmissions == 0)
              return;

            this.loadingAutoTestConclusions = true;
            this.taskService.getAutoTestConclusions(this.taskId).pipe(
              finalize(() => this.loadingAutoTestConclusions = false)
            ).subscribe(
              conclusions => {
                this.autoTestConclusions = conclusions;

                for (let item of this.userSummaries) {
                  // TODO delete old conclusions when reload
                  let unitConclusions = conclusions[item.user.id];
                  if (unitConclusions) {
                    for (let config of this.task.auto_test_configs) {
                      item['_auto_test_conclusion_' + config.id] = unitConclusions[config.id]
                    }
                  }
                }
              },
              error => this.error = error.error
            );

            this.loadingDailySummaries = true;
            this.taskService.getDailySubmissionSummaries(this.taskId).pipe(
              finalize(() => this.loadingDailySummaries = false)
            ).subscribe(
              _summaries => this.dailySummaries = _summaries,
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    );

  }

  goToSubmission(inputID: string, find_by: string, btn: HTMLElement, inputDiv: HTMLElement) {
    let id = parseInt(inputID);
    if (isNaN(id))
      return;

    let query = null;
    switch (find_by) {
      case 'submission_id':
        query = this.submissionService.getSubmission(id);
        break;
      case 'auto_test_id':
        query = this.taskService.findSubmissionByAutoTestID(this.taskId, id);
        break;
    }
    if (query == null)
      return;

    let buttons = inputDiv.querySelectorAll('.button');
    for (let i = 0; i < buttons.length; ++i)
      buttons.item(i).classList.add('disabled');
    btn.classList.add('loading');
    inputDiv.classList.add('disabled');
    query.pipe(
      finalize(() => {
        for (let i = 0; i < buttons.length; ++i)
          buttons.item(i).classList.remove('disabled');
        btn.classList.remove('loading');
        inputDiv.classList.remove('disabled');
      })
    ).subscribe(
      submission => {
        if (submission.task_id != this.taskId) {
          this.error = {msg: 'submission does not belong to this task'};
          return
        }

        this.router.navigate([`${submission.submitter_id}/${submission.id}`], {relativeTo: this.route})
      },
      error => this.error = error.error
    )
  }
}
