import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Submission, SuccessMessage, Task, User} from "../models";
import {TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-my-submissions',
  templateUrl: './my-submissions.component.html',
  styleUrls: ['./my-submissions.component.less']
})
export class MySubmissionsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  submissions: Submission[];
  loadingSubmissions: boolean;

  constructor(
    private accountService: AccountService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) { }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));

    this.loadingSubmissions = true;
    this.taskService.getMySubmissions(this.taskId).pipe(
      finalize(()=>this.loadingSubmissions=false)
    ).subscribe(
      submissions=>this.submissions=submissions,
      error=>this.error=error.error
    )
  }

}
