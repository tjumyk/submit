import {Component, Inject, LOCALE_ID, OnInit} from '@angular/core';
import * as moment from 'moment';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.less']
})
export class AppComponent implements OnInit{

  constructor(
    @Inject(LOCALE_ID) private localeId: string
  ) {
  }

  ngOnInit(){
    moment.locale(this.localeId);
  }
}
