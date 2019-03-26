import {Component, Input, OnInit} from '@angular/core';
import {Pagination} from "../table-util";

@Component({
  selector: 'app-table-pagination-toolbar',
  templateUrl: './table-pagination-toolbar.component.html',
  styleUrls: ['./table-pagination-toolbar.component.less'],
  host: {'class': 'ui segment clearing'}
})
export class TablePaginationToolbarComponent implements OnInit {
  @Input() pagination: Pagination<any>;

  constructor() { }

  ngOnInit() {
  }

}
