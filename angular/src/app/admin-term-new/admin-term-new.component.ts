import { Component, OnInit } from '@angular/core';
import {ErrorMessage} from "../models";
import {NgForm} from "@angular/forms";
import {AdminService, NewTermForm} from "../admin.service";
import {finalize} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-admin-term-new',
  templateUrl: './admin-term-new.component.html',
  styleUrls: ['./admin-term-new.component.less']
})
export class AdminTermNewComponent implements OnInit {
  error: ErrorMessage;
  addingTerm: boolean;
  form:NewTermForm = new NewTermForm();

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
  }

  newTerm(f:NgForm){
    if(f.invalid)
      return;

    this.addingTerm = true;
    this.adminService.addTerm(this.form).pipe(
      finalize(()=>this.addingTerm=false)
    ).subscribe(
      (term)=>this.router.navigate([`../terms/${term.id}`], {relativeTo: this.route}),
      (error)=>this.error = error.error
    )
  }

}
