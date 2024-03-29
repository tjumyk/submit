import {Component, Input, OnInit} from '@angular/core';
import {DailySubmissionSummary, Task} from "../models";

import * as moment from "moment";

@Component({
  selector: 'app-daily-submission-chart',
  templateUrl: './daily-submission-chart.component.html',
  styleUrls: ['./daily-submission-chart.component.less']
})
export class DailySubmissionChartComponent implements OnInit {
  @Input()
  task: Task;
  @Input()
  summaries: DailySubmissionSummary[];

  chartData: any;

  constructor() {
  }

  ngOnInit() {
    if (!this.task || !this.summaries)
      return;

    let firstDay = undefined;
    let lastDay = undefined;
    for (let summary of this.summaries) {
      const m = moment(summary.date);
      summary['_moment'] = m;
      if (!firstDay || m.isBefore(firstDay))
        firstDay = m;
      if (!lastDay || m.isAfter(lastDay))
        lastDay = m;
    }

    // adjust the date range based on the task info
    if (this.task.open_time) {
      const m = moment(this.task.open_time).startOf('day');
      if (m.isBefore(firstDay))
        firstDay = m;
    }
    if (this.task.close_time) {
      const m = moment(this.task.close_time).startOf('day');
      if (m.isAfter(lastDay))
        lastDay = m;
    } else {
      if (this.task.due_time) {
        const m = moment(this.task.due_time).startOf('day');
        if (m.isAfter(lastDay))
          lastDay = m;
      }
    }

    let data = [];
    for (let summary of this.summaries) {
      data.push({x: summary['_moment'], y: summary.total});
    }

    this.chartData = {
      type: 'bar',
      data: {
        datasets: [
          {
            label: 'Daily Submissions',
            data: data
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          xAxes: [
            {
              type: 'time',
              time: {
                unit: 'day',
                min: firstDay,
                max: lastDay,
                tooltipFormat: 'll'
              }
            }
          ],
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0
              }
            }
          ]
        }
      }
    }
  }

}
