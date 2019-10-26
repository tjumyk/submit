import {AfterViewInit, Component, ElementRef, Input, OnInit, ViewChild} from '@angular/core';

// import highlight js and necessary languages
import hljs from 'highlight.js/lib/highlight';
import python from 'highlight.js/lib/languages/python';
import diff from 'highlight.js/lib/languages/diff';
hljs.registerLanguage('python', python);
hljs.registerLanguage('diff', diff);

@Component({
  selector: 'app-code-highlight',
  templateUrl: './code-highlight.component.html',
  styleUrls: ['./code-highlight.component.less']
})
export class CodeHighlightComponent implements OnInit, AfterViewInit {
  @Input()
  code: string;
  @Input()
  language:string;

  @ViewChild('codeElement')
  codeElement: ElementRef;

  constructor() { }

  ngOnInit() {
  }

  ngAfterViewInit(): void {
    hljs.highlightBlock(this.codeElement.nativeElement);
  }

}
