import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Term} from "../models";
import {NgForm} from "@angular/forms";
import {AdminService} from "../admin.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-admin-term-edit',
  templateUrl: './admin-term-edit.component.html',
  styleUrls: ['./admin-term-edit.component.less']
})
export class AdminTermEditComponent implements OnInit {
  error: ErrorMessage;
  loadingTerm: boolean;
  termId: number;
  term: Term;
  updatingTerm: boolean;

  constructor(
    private adminService:AdminService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.termId = parseInt(this.route.snapshot.paramMap.get('team_id'));

    this.loadTerm();
  }

  private loadTerm(){
    this.loadingTerm=true;
    this.adminService.getTerm(this.termId).pipe(
      finalize(()=>this.loadingTerm=false)
    ).subscribe(
      term=>this.term=term,
      error=>this.error=error.error
    )
  }

  updateTerm(f:NgForm){
    if(f.invalid)
      return;

    this.adminService.updateTerm()
  }

}
