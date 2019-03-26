import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Task, UserSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {AllAutoTestConclusionsMap, TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import {SubmissionService} from "../submission.service";
import {makeSortField, Pagination} from "../table-util";
import * as moment from "moment";

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
              item['_last_submit_time'] = moment(item.last_submit_time).unix()
            }
            this.userSummaryPages = new Pagination(summaries, 500);
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
            )
          },
          error => this.error = error.error
        )
      },
      error => this.error = error.error
    );

  }

  goToSubmission(subId: string, btn: HTMLElement, inputDiv: HTMLElement) {
    let id = parseInt(subId);
    if (isNaN(id))
      return;

    btn.classList.add('loading', 'disabled');
    inputDiv.classList.add('disabled');
    this.submissionService.getSubmission(id).pipe(
      finalize(() => {
        btn.classList.remove('loading', 'disabled');
        inputDiv.classList.remove('disabled');
      })
    ).subscribe(
      submission => {
        this.router.navigate([`${submission.submitter_id}/${submission.id}`], {relativeTo: this.route})
      },
      error => this.error = error.error
    )
  }

  bindEnter(event: KeyboardEvent, btn: HTMLElement) {
    if (event.keyCode == 13) {// Enter key
      btn.click()
    }
  }
}
