import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Material, NotebookPreview, Task, Term, User} from "../models";
import {TaskService} from "../task.service";
import {AccountService} from "../account.service";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";
import {MaterialService} from "../material.service";
import {DomSanitizer} from "@angular/platform-browser";
import {finalize} from "rxjs/operators";

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
  numGetNotebookJobs: number;

  materialIcons: { [type: string]: string } = {
    'specification': 'clipboard outline',
    'data': 'database',
    'code': 'code',
    'other': 'copy outline',
    'test environment': 'terminal',
    'solution': 'star outline'
  };

  notebookPreviews: NotebookPreview[][];

  constructor(
    private accountService: AccountService,
    private termService: TermService,
    private taskService: TaskService,
    private materialService: MaterialService,
    private route: ActivatedRoute,
    private sanitizer: DomSanitizer
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

    this.hasPrivateMaterial = false;
    for (let mat of task.materials) {
      if(mat.is_private)
        this.hasPrivateMaterial = true;
    }

    this.setupNotebooksPreview();
  }

  private setupNotebooksPreview() {
    this.numGetNotebookJobs = 0;
    this.notebookPreviews = [];
    for (let mat of this.task.materials) {
      const matNotebooks: NotebookPreview[] = [];
      this.notebookPreviews.push(matNotebooks);  // create an empty list for each material and keep the order

      if (mat.type == 'specification') {
        ++this.numGetNotebookJobs;
        this.materialService.getNotebooks(mat.id).pipe(
          finalize(() => --this.numGetNotebookJobs)
        ).subscribe(
          notebooks => {
            for (let nb of notebooks) {
              nb.material = mat;
              nb.url = this.sanitizer.bypassSecurityTrustResourceUrl(`api/materials/${nb.material_id}/notebooks/${nb.name}/`);
              matNotebooks.push(nb)
            }
          },
          error => this.error = error.error
        );
      }
    }
  }
}
