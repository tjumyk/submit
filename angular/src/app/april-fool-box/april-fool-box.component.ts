import { Component, OnInit } from '@angular/core';
import {finalize} from "rxjs/operators";
import {TermService} from "../term.service";
import {ActivatedRoute} from "@angular/router";
import {Term} from "../models";

@Component({
  selector: 'app-april-fool-box',
  templateUrl: './april-fool-box.component.html',
  styleUrls: ['./april-fool-box.component.less']
})
export class AprilFoolBoxComponent implements OnInit {
  term: Term;

  constructor(private termService: TermService,
              private route: ActivatedRoute) { }

  ngOnInit() {
    const termId = parseInt(this.route.snapshot.paramMap.get('term_id'));
    this.termService.getCachedTerm(termId).subscribe(
      term => {
        this.term = term;
      }
    )
  }

}
