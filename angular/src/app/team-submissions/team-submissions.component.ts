import {Component, OnInit} from '@angular/core';
import {DailySubmissionSummary, ErrorMessage, Task, TeamSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {AllAutoTestConclusionsMap, LastLatePenaltiesResponse, TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {debounceTime, finalize} from "rxjs/operators";
import {SubmissionService} from "../submission.service";
import {makeSortField, Pagination} from "../table-util";
import * as moment from "moment";
import {Subject} from "rxjs";

@Component({
  selector: 'app-team-submissions',
  templateUrl: './team-submissions.component.html',
  styleUrls: ['./team-submissions.component.less']
})
export class TeamSubmissionsComponent implements OnInit {

  error: ErrorMessage;

  taskId: number;
  task: Task;
  teamSummaries: TeamSubmissionSummary[];
  teamSummaryPages: Pagination<TeamSubmissionSummary>;
  totalSubmissions: number;
  loadingSummaries: boolean;
  loadingAutoTestConclusions: boolean;
  autoTestConclusions: AllAutoTestConclusionsMap;

  loadingDailySummaries: boolean;
  dailySummaries: DailySubmissionSummary[];

  loadingLastLatePenalties: boolean;
  lastLatePenalties: LastLatePenaltiesResponse;

  teamSearchKey = new Subject<string>();
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

    this.teamSearchKey.pipe(
      debounceTime(300)
    ).subscribe(
      (key) => this.teamSummaryPages.search(key),
      error => this.error = error.error
    );

    this.taskService.getCachedTask(this.taskId).subscribe(
      task => {
        this.task = task;

        this.loadingSummaries = true;
        this.taskService.getTeamSubmissionSummaries(this.taskId).pipe(
          finalize(() => this.loadingSummaries = false)
        ).subscribe(
          summaries => {
            this.teamSummaries = summaries;

            this.totalSubmissions = 0;
            for (let item of summaries) {
              this.totalSubmissions += item.total_submissions;
              item['_first_submit_time'] = moment(item.first_submit_time).unix();
              item['_last_submit_time'] = moment(item.last_submit_time).unix()
            }
            this.teamSummaryPages = new Pagination(summaries, 500);
            this.teamSummaryPages.setSearchMatcher((item, key) => {
              const keyLower = key.toLowerCase();
              if (item.team.name.toLowerCase().indexOf(keyLower) >= 0)
                return true;
              if (item.team.id.toString().indexOf(keyLower) >= 0)
                return true;
              return false;
            });
            this.sortField = makeSortField(this.teamSummaryPages);

            if (this.totalSubmissions == 0)
              return;

            this.loadingAutoTestConclusions = true;
            this.taskService.getAutoTestConclusions(this.taskId).pipe(
              finalize(() => this.loadingAutoTestConclusions = false)
            ).subscribe(
              conclusions => {
                this.autoTestConclusions = conclusions;

                for (let item of this.teamSummaries) {
                  // TODO delete old conclusions when reload
                  let unitConclusions = conclusions[item.team.id];
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
            );

            this.loadingAutoTestConclusions = true;
            this.taskService.getLastLatePenalties(this.taskId).pipe(
              finalize(() => this.loadingLastLatePenalties = false)
            ).subscribe(
              lastPenalties => {
                this.lastLatePenalties = lastPenalties;

                if(lastPenalties){
                  for (let item of this.teamSummaries) {
                    item['_last_late_penalty'] = lastPenalties[item.team.id];
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

  goToSubmission(subId: string, find_by: string, btn: HTMLElement, inputDiv: HTMLElement) {
    let id = parseInt(subId);
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

    function clear_loading_state() {
      for (let i = 0; i < buttons.length; ++i)
        buttons.item(i).classList.remove('disabled');
      btn.classList.remove('loading');
      inputDiv.classList.remove('disabled');
    }

    for (let i = 0; i < buttons.length; ++i)
      buttons.item(i).classList.add('disabled');
    btn.classList.add('loading');
    inputDiv.classList.add('disabled');
    query.subscribe(
      submission => {
        if (submission.task_id != this.taskId) {
          this.error = {msg: 'submission does not belong to this task'};
          clear_loading_state();
          return
        }

        this.taskService.getTeamAssociation(this.taskId, submission.submitter_id).pipe(
          finalize(() => {
            clear_loading_state();
          })
        ).subscribe(
          ass => {
            if (ass == null) {
              this.error = {msg: 'team association not found'};
              return
            }
            this.router.navigate([`${ass.team_id}/${submission.id}`], {relativeTo: this.route})
          },
          error => this.error = error.error
        )
      },
      error => {
        this.error = error.error;
        clear_loading_state();
      }
    )
  }

}
