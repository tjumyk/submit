import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Task, TeamSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {AllAutoTestConclusionsMap, TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import {SubmissionService} from "../submission.service";

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
  totalSubmissions: number;
  loadingSummaries: boolean;
  loadingAutoTestConclusions: boolean;
  autoTestConclusions: AllAutoTestConclusionsMap;

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
        this.taskService.getTeamSubmissionSummaries(this.taskId).pipe(
          finalize(() => this.loadingSummaries = false)
        ).subscribe(
          summaries => {
            this.teamSummaries = summaries;

            this.totalSubmissions = 0;
            for (let item of summaries) {
              this.totalSubmissions += item.total_submissions;
            }

            this.loadingAutoTestConclusions = true;
            this.taskService.getAutoTestConclusions(this.taskId).pipe(
              finalize(() => this.loadingAutoTestConclusions = false)
            ).subscribe(
              conclusions => this.autoTestConclusions = conclusions,
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
    this.submissionService.getSubmission(id).subscribe(
      submission => {
        if(submission.task_id != this.taskId){
          this.error = {msg: 'submission does not belong to this task'};
          btn.classList.remove('loading', 'disabled');
          inputDiv.classList.remove('disabled');
          return
        }

        this.taskService.getTeamAssociation(this.taskId, submission.submitter_id).pipe(
          finalize(() => {
            btn.classList.remove('loading', 'disabled');
            inputDiv.classList.remove('disabled');
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
        btn.classList.remove('loading', 'disabled');
        inputDiv.classList.remove('disabled');
      }
    )
  }

  bindEnter(event: KeyboardEvent, btn: HTMLElement) {
    if (event.keyCode == 13) {// Enter key
      btn.click()
    }
  }

}
