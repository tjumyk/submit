import {Component, ElementRef, OnInit} from '@angular/core';

@Component({
  selector: 'app-popup-ref',
  templateUrl: './popup-ref.component.html',
  styleUrls: ['./popup-ref.component.less']
})
export class PopupRefComponent implements OnInit {
  el: ElementRef;

  constructor(el: ElementRef) {
    this.el = el;
  }

  ngOnInit() {
  }

}
