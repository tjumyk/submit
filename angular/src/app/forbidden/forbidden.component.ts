import { Component, OnInit } from '@angular/core';
import {TitleService} from "../title.service";

@Component({
  selector: 'app-forbidden',
  templateUrl: './forbidden.component.html',
  styleUrls: ['./forbidden.component.less']
})
export class ForbiddenComponent implements OnInit {

  constructor(
    private titleService: TitleService
  ) { }

  ngOnInit() {
    this.titleService.setTitle('Forbidden')
  }

}
