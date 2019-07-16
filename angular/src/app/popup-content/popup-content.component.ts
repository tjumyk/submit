import {Component, ElementRef, OnInit} from '@angular/core';

@Component({
  selector: 'app-popup-content',
  templateUrl: './popup-content.component.html',
  styleUrls: ['./popup-content.component.less'],
  host: {class: 'ui popup'}
})
export class PopupContentComponent implements OnInit {
  el: ElementRef;
  create: boolean;

  constructor(el: ElementRef) {
    this.el = el;
  }

  ngOnInit() {
  }

}
