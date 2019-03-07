import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Task, UserSubmissionSummary} from "../models";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";
import {ActivatedRoute, Router} from "@angular/router";
import {finalize} from "rxjs/operators";
import {SubmissionService} from "../submission.service";

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
  totalSubmissions: number;
  totalSubmittedUsers: number;
  loadingSummaries: boolean;

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
            this.totalSubmittedUsers = 0;
            for (let item of summaries) {
              this.totalSubmissions += item.total_submissions;
              this.totalSubmittedUsers += 1;
            }
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
