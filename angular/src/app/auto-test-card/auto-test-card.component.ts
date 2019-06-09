import {Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {AutoTest, AutoTestConfig, ErrorMessage} from "../models";
import {SubmissionService} from "../submission.service";
import {printDuration} from "../time-util";
import * as moment from "moment";
import {finalize} from "rxjs/operators";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-auto-test-card',
  templateUrl: './auto-test-card.component.html',
  styleUrls: ['./auto-test-card.component.less'],
  host: {'class': 'ui segments'}
})
export class AutoTestCardComponent implements OnInit {
  @Input() test: AutoTest;
  @Input() config: AutoTestConfig;

  @Input() isAdmin: boolean;
  @Output() deleted: EventEmitter<any> = new EventEmitter();
  @Output() error: EventEmitter<ErrorMessage> = new EventEmitter();

  @ViewChild('detailsPanel')
  detailsPanel: ElementRef;

  getStatusColor: (status: string) => string;
  getStatusClass: (status: string) => string;
  extractConclusion: (test: AutoTest, config: AutoTestConfig) => any;
  printConclusion: (test: AutoTest, config: AutoTestConfig) => any;
  renderResultHTML: (test: AutoTest, config: AutoTestConfig) => string;

  showDetails: boolean;

  constructor(
    private adminService: AdminService,
    private submissionService: SubmissionService
  ) {
    /* use closures to avoid scope error */
    this.getStatusColor = status => submissionService.getAutoTestStatusColor(status);
    this.getStatusClass = status =>submissionService.getAutoTestStatusClass(status);
    this.extractConclusion = (test, config) => submissionService.extractConclusion(test, config);
    this.printConclusion = (test, config) => submissionService.printConclusion(test, config);
    this.renderResultHTML = (test, config) => submissionService.renderResultHTML(test, config);
  }

  ngOnInit() {
  }

  computeDuration(start_time, end_time) {
    return printDuration(moment(end_time).diff(moment(start_time), 'seconds'))
  }

  deleteAutoTest(test: AutoTest, btn: HTMLElement) {
    if (!confirm(`Really want to delete test ${test.id}?`))
      return;

    btn.classList.add('disabled');
    this.adminService.deleteAutoTest(test.submission_id, test.id).pipe(
      finalize(() => btn.classList.remove('disabled'))
    ).subscribe(
      () => this.deleted.emit(null),
      error => this.error.emit(error.error)
    )
  }

  toggleDetails(){
    const animationDelay = 300;

    if(!this.showDetails){
      this.showDetails = true; // let angular create the element first
      setTimeout(()=>{
        if(this.detailsPanel){
          const element = this.detailsPanel.nativeElement;
          element.style.height = element.scrollHeight + 'px';
          element.classList.add('visible');

          setTimeout(()=>{
            if(this.detailsPanel)
              this.detailsPanel.nativeElement.style.height = '';
          }, animationDelay)
        }
      })
    }else{
      if(this.detailsPanel){
        const element = this.detailsPanel.nativeElement;
        element.style.height = element.scrollHeight + 'px';
        element.classList.remove('visible');

        setTimeout(()=>{
          element.style.height = '0';
          setTimeout(()=>{
            this.showDetails = false; // let angular destroy the element
          }, animationDelay)
        });
      }
    }
  }
}
