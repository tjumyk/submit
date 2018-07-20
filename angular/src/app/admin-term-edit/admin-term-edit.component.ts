import {Component, OnInit} from '@angular/core';
import {ErrorMessage, Group, SuccessMessage, Term} from "../models";
import {AdminService} from "../admin.service";
import {ActivatedRoute} from "@angular/router";
import {debounceTime, distinctUntilChanged, finalize, switchMap} from "rxjs/operators";
import {Subject} from "rxjs/internal/Subject";
import {of} from "rxjs/internal/observable/of";

@Component({
  selector: 'app-admin-term-edit',
  templateUrl: './admin-term-edit.component.html',
  styleUrls: ['./admin-term-edit.component.less']
})
export class AdminTermEditComponent implements OnInit {
  error: ErrorMessage;
  success: SuccessMessage;
  loadingTerm: boolean;
  termId: number;
  term: Term;

  private searchGroupNames = new Subject<string>();
  searchGroupResults: Group[];

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.termId = parseInt(this.route.snapshot.paramMap.get('team_id'));

    this.loadTerm();
    this.setupGroupSearch();
  }

  private loadTerm() {
    this.loadingTerm = true;
    this.adminService.getTerm(this.termId).pipe(
      finalize(() => this.loadingTerm = false)
    ).subscribe(
      term => this.term = term,
      error => this.error = error.error
    )
  }

  private setupGroupSearch() {
    this.searchGroupNames.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((name: string) => {
        if (!name)
          return of(null);
        return this.adminService.searchGroupsByName(name, 10)
      })
    ).subscribe(
      (results) => this.searchGroupResults = results,
      (error) => this.error = error.error
    );
  }

  searchGroup(name: string){
    this.searchGroupNames.next(name);
  }

}
