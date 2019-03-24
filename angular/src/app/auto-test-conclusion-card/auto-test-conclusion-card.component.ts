import {Component, Input, OnInit} from '@angular/core';
import {AutoTestConclusionsMap} from "../task.service";
import {Task} from "../models";

@Component({
  selector: 'app-auto-test-conclusion-card',
  templateUrl: './auto-test-conclusion-card.component.html',
  styleUrls: ['./auto-test-conclusion-card.component.less']
})
export class AutoTestConclusionCardComponent implements OnInit {
  @Input() task: Task;
  @Input() conclusions: AutoTestConclusionsMap;

  constructor() { }

  ngOnInit() {
  }

}
