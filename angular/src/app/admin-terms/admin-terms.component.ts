import { Component, OnInit } from '@angular/core';
import {ErrorMessage, Term} from "../models";
import {AdminService} from "../admin.service";
import {finalize} from "rxjs/operators";

@Component({
  selector: 'app-admin-terms',
  templateUrl: './admin-terms.component.html',
  styleUrls: ['./admin-terms.component.less']
})
export class AdminTermsComponent implements OnInit {
  error: ErrorMessage;
  loadingTerms: boolean;
  terms: Term[];

  constructor(
    private adminService: AdminService
  ) { }

  ngOnInit() {
    this.loadTerms();
  }

  private loadTerms(){
    this.loadingTerms = true;
    this.adminService.getTerms().pipe(
      finalize(()=>this.loadingTerms=false)
    ).subscribe(
      (terms) => this.terms = terms,
      (error)=> this.error = error.error
    )
  }

  deleteTerm(term, index, btn:HTMLElement){
    if(!confirm(`Really want to delete term ${term.title}? This is not recoverable!`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteTerm(term.id).pipe(
      finalize(()=>btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      ()=>this.terms.splice(index, 1),
      (error)=>this.error=error.error
    )
  }

}
