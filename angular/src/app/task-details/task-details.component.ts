import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Material, SuccessMessage, Task, Term, User} from "../models";
import {TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";

export class MaterialCategory {
  type: string;
  icon: string;
  items: Material[];
}

@Component({
  selector: 'app-task-detail',
  templateUrl: './task-details.component.html',
  styleUrls: ['./task-details.component.less']
})
export class TaskDetailsComponent implements OnInit {
  error: ErrorMessage;

  taskId: number;
  task: Task;
  user: User;
  termId: number;
  term: Term;
  accessRoles: Set<string>;

  hasPrivateMaterial: boolean = false;
  materialCategories: MaterialCategory[];
  materialCategoriesTemplate: MaterialCategory[] = [
    {
      type: 'specification',
      icon: 'clipboard outline',
      items: []
    },
    {
      type: 'data',
      icon: 'database',
      items: []
    },
    {
      type: 'code',
      icon: 'code',
      items: []
    },
    {
      type: 'other',
      icon: 'copy outline',
      items: []
    },
    {
      type: 'test environment',
      icon: 'terminal',
      items: []
    },
    {
      type: 'solution',
      icon: 'star outline',
      items: []
    },
  ];

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private taskService: TaskService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;

        this.termId = parseInt(this.route.snapshot.parent.parent.paramMap.get('term_id'));
        this.termService.getCachedTerm(this.termId).subscribe(
          term => {
            this.term = term;
            this.accessRoles = TermService.getAccessRoles(this.term, this.user);

            this.taskId = parseInt(this.route.snapshot.parent.paramMap.get('task_id'));
            this.taskService.getCachedTask(this.taskId).subscribe(
              task => this.setupTask(task),
              error => this.error = error.error
            )
          },
          error => this.error = error.error
        );
      },
      error => this.error = error.error
    );
  }

  private setupTask(task: Task) {
    this.task = task;

    const categories: { [key: string]: Material[] } = {};
    this.hasPrivateMaterial = false;
    for (let mat of task.materials) {
      if(mat.is_private)
        this.hasPrivateMaterial = true;
      let list = categories[mat.type];
      if (list == null) {
        categories[mat.type] = list = [];
      }
      list.push(mat)
    }
    this.materialCategories = [];
    for (let cat of this.materialCategoriesTemplate) {
      const items = categories[cat.type];
      if (items != null)
        this.materialCategories.push({
          type: cat.type,
          icon: cat.icon,
          items: items
        })
    }
  }

}
