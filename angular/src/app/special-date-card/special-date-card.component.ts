import {Component, OnDestroy, OnInit} from '@angular/core';
import * as moment from "moment";

@Component({
  selector: 'app-special-date-card',
  templateUrl: './special-date-card.component.html',
  styleUrls: ['./special-date-card.component.less']
})
export class SpecialDateCardComponent implements OnInit, OnDestroy {
  specialDate: string;
  checkerHandler: number;

  constructor() {
  }

  ngOnInit() {
    const checker = () => {
      const now = moment();
      const month = now.get('month') + 1;
      const day = now.get('date');

      if (month == 4 && day == 1) {
        this.specialDate = 'april-fool';
        return;
      }
      if (month == 10 && day == 31) {
        this.specialDate = 'halloween';
        return;
      }
      this.specialDate = undefined;
    };
    checker();
    this.checkerHandler = setInterval(checker, 10 * 60 * 1000);
  }

  ngOnDestroy(): void {
    clearInterval(this.checkerHandler);
  }
}
