import {Component, Input, OnInit} from '@angular/core';
import {AllAutoTestConclusionsMap} from "../task.service";
import {AutoTestConfig, Task} from "../models";
import {AutoTestConfigTypeInfo, SubmissionService} from "../submission.service";

interface SummaryData {
  config: AutoTestConfig;
  chartData: any;
}

const colors = {
  default: 'rgba(0, 0, 0, 0.1)',
  red: '#db2828',
  orange: '#f2711c',
  yellow: '#fbbd08',
  olive: '#b5cc18',
  green: '#21ba45',
  teal: '#00b5ad',
  blue: '#2185d0',
  violet: '#6435c9',
  purple: '#a333c8',
  pink: '#e03997',
  brown: '#a5673f',
  grey: '#767676',
  black: '#1b1c1d'
};

const colorScheme = [
  colors.blue,
  colors.orange,
  colors.red,
  colors.olive,
  colors.green,
  colors.yellow,
  colors.violet,
  colors.pink,
  colors.brown,
  colors.grey
];

const antiPlagiarismLevels = [
  {name: 'No Evidence', color: colors.green},
  {name: 'Weak Evidence', color: colors.olive},
  {name: 'Moderate Evidence', color: colors.yellow},
  {name: 'Strong Evidence', color: colors.orange},
  {name: 'Very Strong Evidence', color: colors.red},
  {name: 'Full Copy', color: colors.purple},
  {name: 'Same Code', color: colors.violet},
  {name: 'Same File', color: colors.black}
];

@Component({
  selector: 'app-auto-test-conclusion-summary-charts',
  templateUrl: './auto-test-conclusion-summary-charts.component.html',
  styleUrls: ['./auto-test-conclusion-summary-charts.component.less']
})
export class AutoTestConclusionSummaryChartsComponent implements OnInit {
  @Input()
  task: Task;
  @Input()
  conclusions: AllAutoTestConclusionsMap;

  gridClass: string;
  data: SummaryData[];

  autoTestConfigTypes: { [id: string]: AutoTestConfigTypeInfo };

  constructor(private submissionService: SubmissionService) {
    this.autoTestConfigTypes = submissionService.autoTestConfigTypes;
  }

  ngOnInit() {
    if (!this.task || !this.conclusions)
      return;

    const conclusionList = Object.values(this.conclusions);

    this.data = [];
    for (let config of this.task.auto_test_configs) {
      if (config.result_conclusion_type == 'json') // skip json type results
        continue;

      const results = [];
      for (let conclusion of conclusionList)
        results.push(conclusion[config.id]);

      let chartData;
      switch (config.result_conclusion_type) {
        case 'int':
        case 'float':
          chartData = this.buildBarChart(this.task, results);
          break;
        case 'bool':
        case 'string':
          chartData = this.buildPieChart(config, results);
          break;
      }
      if (chartData) {
        this.data.push({
          config,
          chartData
        })
      }
    }

    // decide grid columns
    switch (this.data.length) {
      case 0:
        this.gridClass = 'empty';
        break;
      case 1:
        this.gridClass = 'one column';
        break;
      case 2:
        this.gridClass = 'two column';
        break;
      default:
        this.gridClass = 'three column'
    }
  }

  private buildBarChart(task: Task, results: number[]) {
    let numbers = new Set<number>();
    let numberCounts = {};
    let noResultCount = 0;
    let nanCount = 0;
    for (let v of results) {
      if (v === null || v === undefined) {
        ++noResultCount;
        continue;
      }
      if (isNaN(v)) {
        ++nanCount;
        continue;
      }
      if (numbers.has(v))
        ++numberCounts[v];
      else {
        numbers.add(v);
        numberCounts[v] = 1;
      }
    }

    let numberList = Array.from(numbers).sort((a, b) => a - b);
    let labels = [];
    let data = [];
    for (let v of numberList) {
      labels.push('' + v);
      data.push(numberCounts[v])
    }

    if (nanCount > 0) {
      labels.unshift('NaN');
      data.unshift(nanCount);
    }

    if (noResultCount > 0) {
      labels.unshift('N/A');
      data.unshift(noResultCount);
    }

    let datasetLabel;
    if (task.is_team_task)
      datasetLabel = 'Teams';
    else
      datasetLabel = 'Users';

    return {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: datasetLabel,
            data: data
          }
        ]
      },
      options: {
        maintainAspectRatio: false,
        scales: {
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

  private buildPieChart(config: AutoTestConfig, results: any[]) {
    const boolMode = config.result_conclusion_type == 'bool';

    let resultCounts = {};
    let noResultCount = 0;
    for (let v of results) {
      if (v === null || v === undefined) {
        ++noResultCount;
        continue;
      }
      if (boolMode) // enforce the values be either 'true' or 'false'
        v = v ? 'true' : 'false';

      const count = resultCounts[v];
      if (count === undefined) {
        resultCounts[v] = 1
      } else {
        resultCounts[v] = count + 1;
      }
    }

    let labels: string[];
    let bgColors;
    if (boolMode) {
      labels = ['true', 'false'];
      bgColors = [colors.green, colors.red];
    } else {
      if (config.type == 'anti-plagiarism') {
        labels = [];
        bgColors = [];
        const remainKeys = new Set(Object.keys(resultCounts));
        for (let level of antiPlagiarismLevels) {
          if (resultCounts[level.name] === undefined)
            continue;
          labels.push(level.name);
          bgColors.push(level.color);
          remainKeys.delete(level.name);
        }

        if(remainKeys.size > 0){ // fallback for any unexpected additional keys
          let i = 0;
          for(let k of Array.from(remainKeys).sort()){
            labels.push(k);
            bgColors.push(colorScheme[i % colorScheme.length]);
            ++i;
          }
        }
      } else {
        labels = Object.keys(resultCounts).sort();
        bgColors = [];
        let i = 0;
        for (let key in resultCounts) {
          bgColors.push(colorScheme[i % colorScheme.length]);
          ++i;
        }
      }
    }

    let data = [];
    for (let key of labels) {
      data.push(resultCounts[key])
    }

    if (noResultCount > 0) {
      labels.unshift('No Result');
      data.unshift(noResultCount);
      bgColors.unshift(colors.default);
    }

    return {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [
          {
            data: data,
            backgroundColor: bgColors
          }
        ]
      },
      options: {
        maintainAspectRatio: false
      }
    }
  }
}
