import {AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild} from '@angular/core';
import {NotebookPreview} from "../models";
import * as katex from "katex";
import renderMathInElement from 'katex/dist/contrib/auto-render';


@Component({
  selector: 'app-notebook-view',
  templateUrl: './notebook-view.component.html',
  styleUrls: ['./notebook-view.component.less'],
  host: {'class': 'ui segment notebook-view'}
})
export class NotebookViewComponent implements OnInit, AfterViewInit {
  @Input()
  notebook: NotebookPreview;

  @ViewChild('body')
  body: ElementRef<HTMLElement>;

  constructor() {
  }

  ngOnInit() {
  }

  ngAfterViewInit() {
    if (!this.body || !this.body.nativeElement)
      return;
    const body = this.body.nativeElement;
    renderMathInElement(body, {
      delimiters: [
        {left: "$$", right: "$$", display: true},
        {left: "$", right: "$", display: false},
        {left: "\\(", right: "\\)", display: false},
        {left: "\\[", right: "\\]", display: true}
      ]
    });
  }
}
