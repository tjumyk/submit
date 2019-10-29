import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {
  AutoTest,
  AutoTestConfig,
  ErrorMessage,
  FileRequirement,
  Material,
  Submission,
  Task,
  User
} from "../models";
import {AutoTestConfigTypeInfo, SubmissionService} from "../submission.service";
import {finalize} from "rxjs/operators";
import {AccountService} from "../account.service";
import {AdminService} from "../admin.service";

@Component({
  selector: 'app-submission-auto-tests-view',
  templateUrl: './submission-auto-tests-view.component.html',
  styleUrls: ['./submission-auto-tests-view.component.less']
})
export class SubmissionAutoTestsViewComponent implements OnInit, OnDestroy {
  @Input()
  task: Task;
  @Input()
  submission: Submission;
  @Input()
  apiBase: string;

  @Output()
  error: EventEmitter<ErrorMessage> = new EventEmitter();

  autoTestConfigTypes: {[id: string]: AutoTestConfigTypeInfo};

  user: User;
  isAdmin: boolean;

  firstLoadComplete: boolean;

  // some indices
  materials: {[id: number]: Material} = {};
  file_requirements: {[id: number]: FileRequirement} = {};
  configs: { [id: number]: AutoTestConfig } = {};
  autoTests: { [id: number]: AutoTest } = {};

  // grouped tests
  autoTestGroups: { [config_id: number]: AutoTest[] } = {};

  autoTestsTrackerHandler: number;

  constructor(
    private accountService: AccountService,
    private adminService: AdminService,
    private submissionService: SubmissionService
  ) {
    this.apiBase = submissionService.api; // this default api is only for admins or tutors
    this.autoTestConfigTypes = submissionService.autoTestConfigTypes;
  }

  ngOnInit() {
    this.accountService.getCurrentUser().subscribe(
      user => {
        this.user = user;
        this.isAdmin = AccountService.isAdmin(user);

        this.setup();
      }
    );
  }

  ngOnDestroy(): void {
    clearInterval(this.autoTestsTrackerHandler);
  }

  setup() {
    for( let mat of this.task.materials){
      this.materials[mat.id] = mat;
    }
    for(let req of this.task.file_requirements){
      this.file_requirements[req.id] = req;
    }
    for (let config of this.task.auto_test_configs) {
      this.setupConfig(config);
      this.autoTestGroups[config.id] = []; // init test groups
      this.configs[config.id] = config; // init config map
    }

    let firstLoad = true;
    let updateAfterTimestamp = undefined;

    const autoTestsTracker = () => {
      let needRefresh = false;
      if (firstLoad) {
        needRefresh = true;
        firstLoad = false;
      } else {
        for (let id in this.autoTests) {
          const test = this.autoTests[id];
          if (!test.final_state) {
            needRefresh = true;
            break;
          }
        }
      }
      if (!needRefresh) {
        // this tracker still need to run in the background as new test may be created, so don't clearInterval here.
        return; // skip request since all (current) works finished
      }

      this.submissionService.getAutoTestAndResults(this.submission.id, this.apiBase, updateAfterTimestamp).subscribe(
        testList => {
          this.firstLoadComplete = true;

          let tests: AutoTest[];
          if(testList.hasOwnProperty('timestamp')){  // new dict format
            updateAfterTimestamp = testList.timestamp;
            tests = testList.tests;
          }else{  // old list format
            tests = testList;
          }

          for (let test of tests) {
            const config = this.configs[test.config_id];
            if (!config) {  // TODO load new config
              console.warn(`ignoring test ${test.id} as its config is not loaded`);
              continue; // currently ignore it to avoid problems
            }

            let oldTest = this.autoTests[test.id];
            if (oldTest) { // test already exists, we need to update the old test
              oldTest.work_id = test.work_id;

              oldTest.hostname = test.hostname;
              oldTest.pid = test.pid;

              oldTest.state = test.state;
              oldTest.final_state = test.final_state;
              oldTest.result = test.result;
              oldTest.exception_class = test.exception_class;
              oldTest.exception_message = test.exception_message;
              oldTest.exception_traceback = test.exception_traceback;

              oldTest.created_at= test.created_at;
              oldTest.modified_at = test.modified_at;
              oldTest.started_at = test.started_at;
              oldTest.stopped_at = test.stopped_at;

              oldTest.output_files = test.output_files;

              oldTest.pending_tests_ahead = test.pending_tests_ahead;
            } else { // new test
              this.autoTestGroups[test.config_id].push(test);  // note the group must have been created
              this.autoTests[test.id] = test;
            }
          }
        },
        error => {
          this.error.emit(error.error);
          clearInterval(this.autoTestsTrackerHandler);  // stop further checks
        }
      )
    };

    autoTestsTracker();
    this.autoTestsTrackerHandler = setInterval(autoTestsTracker, 5000);
  }

  setupConfig(config: AutoTestConfig){
    config.template_file = this.materials[config.template_file_id];
    config.file_requirement = this.file_requirements[config.file_requirement_id];
    config.environment = this.materials[config.environment_id];
  }

  runNewTest(config: AutoTestConfig, btn: HTMLElement) {
    btn.classList.add('loading', 'disabled');
    this.adminService.runAutoTest(this.submission.id, config.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      test => {
        this.autoTestGroups[test.config_id].push(test);  // note the group must have been created
        this.autoTests[test.id] = test;
      },
      error => this.error.emit(error.error)
    )
  }

  onAutoTestDeleted(test: AutoTest) {
    delete this.autoTests[test.id];

    const group = this.autoTestGroups[test.config_id];
    let index = 0;
    for (let _test of group) { // use id match to avoid async update issue
      if (_test.id == test.id) {
        group.splice(index, 1);
        break;
      }
      ++index;
    }
  }

}
