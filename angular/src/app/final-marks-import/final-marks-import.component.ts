import {Component, OnInit} from '@angular/core';
import {ErrorMessage, SuccessMessage} from "../models";
import {Subject} from "rxjs";
import {AccountService} from "../account.service";
import {TaskService} from "../task.service";
import {ActivatedRoute} from "@angular/router";
import {debounceTime, finalize} from "rxjs/operators";
import {AdminService} from "../admin.service";

export class Table {
  columns: TableColumn[] = [];
  data: string[][] = [];
}

export class TableColumn {
  index: number;
  head: string;
}

@Component({
  selector: 'app-final-marks-import',
  templateUrl: './final-marks-import.component.html',
  styleUrls: ['./final-marks-import.component.less']
})
export class FinalMarksImportComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;

  taskId: number;
  isAdmin: boolean;

  submitting: boolean;

  input = new Subject<string>();
  table: Table = new Table();
  hasHeader: boolean = undefined;
  userColumn: TableColumn;
  marksColumn: TableColumn;
  commentColumn: TableColumn;

  constructor(private accountService: AccountService,
              private taskService: TaskService,
              private adminService: AdminService,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.parent.parent.paramMap.get('task_id'));

    this.input.pipe(
      debounceTime(300)
    ).subscribe(
      data => this.processInput(data),
      error => this.error = error.error
    );
  }

  private processInput(data: string) {
    this.table = this.parseTable(data);

    // detect if table has header
    if (this.hasHeader === undefined) {
      this.hasHeader = false;
      let keywords = new Set(['id', 'name', 'user name', 'username', 'userid']);
      for (let col of this.table.columns) {
        if (keywords.has(col.head.toLowerCase())) {
          this.hasHeader = true;
          break;
        }
      }
    }

    // update selected target columns
    if (this.userColumn)
      this.userColumn = this.table.columns[this.userColumn.index];
    if (this.marksColumn)
      this.marksColumn = this.table.columns[this.marksColumn.index];
    if (this.commentColumn)
      this.commentColumn = this.table.columns[this.commentColumn.index];
  }

  private parseTable(data: string): Table {
    let lines = [];
    let columns = [];
    for (let line of data.split('\n')) {
      line = line.trim();
      if (!line)
        continue;
      let fields = [];
      for (let field of line.split('\t')) {
        fields.push(field.trim());
      }

      if (!lines.length) {
        let i = 0;
        for (let field of fields) {
          let column = new TableColumn();
          column.index = i;
          column.head = field;
          columns.push(column);
          ++i;
        }
      }

      lines.push(fields);
    }
    let table = new Table();
    table.data = lines;
    table.columns = columns;
    return table;
  }

  submit() {
    if (!this.userColumn || !this.marksColumn) {
      return;
    }

    this.submitting = true;
    this.success = undefined;
    let request = [];
    let i = 0;
    let entry;
    for (let row of this.table.data) {
      if (i == 0 && this.hasHeader) {
        ++i;
        continue;
      }
      entry = [row[this.userColumn.index], parseFloat(row[this.marksColumn.index]), null];
      if (this.commentColumn)
        entry[2] = row[this.commentColumn.index];
      request.push(entry);
      ++i;
    }
    this.adminService.batchSetFinalMarks(this.taskId, request).pipe(
      finalize(() => this.submitting = false)
    ).subscribe(
      resp => {
        this.success = {msg: `Submitted successfully: ${resp.new} added, ${resp.updated} updated`}
      },
      error => this.error = error.error
    )
  }

}
