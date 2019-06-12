import {Component, Input, OnInit} from '@angular/core';
import {AutoTestConclusionsMap} from "../task.service";
import {Task} from "../models";

@Component({
  selector: 'app-auto-test-conclusions-card',
  templateUrl: './auto-test-conclusions-card.component.html',
  styleUrls: ['./auto-test-conclusions-card.component.less']
})
export class AutoTestConclusionsCardComponent implements OnInit {
  @Input() task: Task;
  @Input() conclusions: AutoTestConclusionsMap;

  constructor() { }

  ngOnInit() {
  }

}
