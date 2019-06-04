import { Component, OnInit } from '@angular/core';
import {Location} from "@angular/common";
import {ErrorMessage, QAndA} from "../models";
import {MetaService} from "../meta.service";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-help',
  templateUrl: './help.component.html',
  styleUrls: ['./help.component.less']
})
export class HelpComponent implements OnInit {
  error: ErrorMessage;

  loadingFAQ: boolean;
  faq: QAndA[];

  constructor(
    private location: Location,
    private metaService: MetaService
  ) { }

  ngOnInit() {
    this.loadingFAQ = true;
    this.metaService.getFAQ().pipe(
      finalize(()=>this.loadingFAQ=false)
    ).subscribe(
      faq =>this.faq = faq,
      error=>this.error= error.error
    )
  }

  navigateBack(){
    this.location.back()
  }
}
