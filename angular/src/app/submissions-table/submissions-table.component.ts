import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {AutoTest, Submission, SubmissionStatus, Task} from "../models";
import {LastAutoTestsMap} from "../task.service";
import * as moment from "moment";
import {LatePenalty} from "../late-penalty";

@Component({
  selector: 'app-submissions-table',
  templateUrl: './submissions-table.component.html',
  styleUrls: ['./submissions-table.component.less']
})
export class SubmissionsTableComponent implements OnInit, OnChanges {
  @Input() task: Task;
  @Input() status: SubmissionStatus;
  @Input() submissions: Submission[];
  @Input() lastAutoTests: LastAutoTestsMap;

  rowOffset: number;

  constructor() {
  }

  ngOnInit() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    this.setUp()
  }

  setUp() {
    // check task
    if (!this.task)
      return;

    // check status
    if (!this.status)
      return;
    if (this.task.is_team_task && (!this.status.team_association || !this.status.team_association.team.is_finalised))
      return;

    // check submissions
    if (!this.submissions)
      return;

    // decide attempt offset
    if (this.task.submission_history_limit != null) {
      this.rowOffset = Math.max(0, this.status.attempts - this.submissions.length)
    } else {
      this.rowOffset = 0;
    }

    // compute penalty
    const penalty = LatePenalty.parse(this.task.late_penalty);
    let dueMoment = moment(this.task.due_time);
    if (this.status.special_consideration && this.status.special_consideration.due_time_extension) {
      dueMoment.add(this.status.special_consideration.due_time_extension, 'hour');
    }
    for (let sub of this.submissions) {
      const submitMoment = moment(sub.created_at);
      if (submitMoment.isAfter(dueMoment)) {
        const lateDays = Math.ceil(submitMoment.diff(dueMoment, 'day', true));
        sub['_lateDays'] = lateDays;
        if (penalty) {
          sub['_latePenalty'] = penalty.getPenalty(lateDays);
        }
      }
    }
  }
}
