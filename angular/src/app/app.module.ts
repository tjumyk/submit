import {BrowserModule} from '@angular/platform-browser';
import {LOCALE_ID, NgModule} from '@angular/core';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {AdminComponent} from './admin/admin.component';
import {AdminTermEditComponent} from './admin-term-edit/admin-term-edit.component';
import {HttpClientModule} from "@angular/common/http";
import {FormsModule} from "@angular/forms";
import {HomeComponent} from './home/home.component';
import {ForbiddenComponent} from "./forbidden/forbidden.component";
import {NotFoundComponent} from "./not-found/not-found.component";
import {ErrorMessageComponent} from './error-message/error-message.component';
import {AdminCoursesComponent} from './admin-courses/admin-courses.component';
import {AdminCourseEditComponent} from './admin-course-edit/admin-course-edit.component';
import {AdminCourseNewComponent} from './admin-course-new/admin-course-new.component';
import {SuccessMessageComponent} from './success-message/success-message.component';
import {AdminAccountsComponent} from './admin-accounts/admin-accounts.component';
import {AdminTaskEditComponent} from './admin-task-edit/admin-task-edit.component';

import {TermComponent} from './term/term.component';
import {TaskComponent} from './task/task.component';
import {TeamComponent} from './team/team.component';
import {SubmitComponent} from './submit/submit.component';
import {TeamsComponent} from './teams/teams.component';
import {SizePipe} from './size.pipe';
import {TasksComponent} from './tasks/tasks.component';
import {TaskDetailsComponent} from './task-details/task-details.component';
import {SubmissionsComponent} from './submissions/submissions.component';
import {MySubmissionsComponent} from './my-submissions/my-submissions.component';
import {MySubmissionDetailsComponent} from './my-submission-details/my-submission-details.component';
import {SubmissionDetailsComponent} from './submission-details/submission-details.component';
import {MyTeamComponent} from './my-team/my-team.component';
import {MyTeamSubmissionsComponent} from './my-team-submissions/my-team-submissions.component';
import {MyTeamSubmissionDetailsComponent} from './my-team-submission-details/my-team-submission-details.component';
import {TeamSubmissionsComponent} from './team-submissions/team-submissions.component';
import {TeamSubmissionDetailsComponent} from './team-submission-details/team-submission-details.component';
import {SubmissionListComponent} from './submission-list/submission-list.component';
import {TeamSubmissionListComponent} from './team-submission-list/team-submission-list.component';
import {JoinOrCreateTeamComponent} from './join-or-create-team/join-or-create-team.component';
import {TaskPreviewComponent} from './task-preview/task-preview.component';
import {TaskDetailsPreviewComponent} from './task-details-preview/task-details-preview.component';
import { OrdinalPipe } from './ordinal.pipe';
import { AutoTestCardComponent } from './auto-test-card/auto-test-card.component';
import { AutoTestMiniCardComponent } from './auto-test-mini-card/auto-test-mini-card.component';
import { SubmissionsTableComponent } from './submissions-table/submissions-table.component';
import { AutoTestConclusionsCardComponent } from './auto-test-conclusions-card/auto-test-conclusions-card.component';
import { TablePaginationToolbarComponent } from './table-pagination-toolbar/table-pagination-toolbar.component';
import { RunAutoTestCardComponent } from './run-auto-test-card/run-auto-test-card.component';
import { MessagesComponent } from './messages/messages.component';
import { HelpComponent } from './help/help.component';
import { AboutComponent } from './about/about.component';
import { MessageDetailComponent } from './message-detail/message-detail.component';
import { EmailSubscriptionsComponent } from './email-subscriptions/email-subscriptions.component';
import { UserMiniCardComponent } from './user-mini-card/user-mini-card.component';
import { SubmissionCardComponent } from './submission-card/submission-card.component';
import { SubmissionAutoTestsViewComponent } from './submission-auto-tests-view/submission-auto-tests-view.component';
import { PopupComponent } from './popup/popup.component';
import { PopupRefComponent } from './popup-ref/popup-ref.component';
import { PopupContentComponent } from './popup-content/popup-content.component';
import { DailySubmissionChartComponent } from './daily-submission-chart/daily-submission-chart.component';
import { AutoTestConclusionSummaryChartsComponent } from './auto-test-conclusion-summary-charts/auto-test-conclusion-summary-charts.component';
import { ChartComponent } from './chart/chart.component';
import { CodeHighlightComponent } from './code-highlight/code-highlight.component';
import { FileDiffLabelComponent } from './file-diff-label/file-diff-label.component';
import { HalloweenPumpkinComponent } from './halloween-pumpkin/halloween-pumpkin.component';
import { SpecialDateCardComponent } from './special-date-card/special-date-card.component';
import { AprilFoolBoxComponent } from './april-fool-box/april-fool-box.component';
import { SubmissionCommentsViewComponent } from './submission-comments-view/submission-comments-view.component';
import { CommentsComponent } from './comments/comments.component';

@NgModule({
  declarations: [
    AppComponent,
    AdminComponent,
    AdminTermEditComponent,
    HomeComponent,
    ForbiddenComponent,
    NotFoundComponent,
    ErrorMessageComponent,
    AdminCoursesComponent,
    AdminCourseEditComponent,
    AdminCourseNewComponent,
    SuccessMessageComponent,
    AdminAccountsComponent,
    AdminTaskEditComponent,
    TermComponent,
    TaskComponent,
    TeamComponent,
    SubmitComponent,
    TeamsComponent,
    SizePipe,
    TasksComponent,
    TaskDetailsComponent,
    SubmissionsComponent,
    MySubmissionsComponent,
    MySubmissionDetailsComponent,
    SubmissionDetailsComponent,
    MyTeamComponent,
    MyTeamSubmissionsComponent,
    MyTeamSubmissionDetailsComponent,
    TeamSubmissionsComponent,
    TeamSubmissionDetailsComponent,
    SubmissionListComponent,
    TeamSubmissionListComponent,
    JoinOrCreateTeamComponent,
    TaskPreviewComponent,
    TaskDetailsPreviewComponent,
    OrdinalPipe,
    AutoTestCardComponent,
    AutoTestMiniCardComponent,
    SubmissionsTableComponent,
    AutoTestConclusionsCardComponent,
    TablePaginationToolbarComponent,
    RunAutoTestCardComponent,
    MessagesComponent,
    HelpComponent,
    AboutComponent,
    MessageDetailComponent,
    EmailSubscriptionsComponent,
    UserMiniCardComponent,
    SubmissionCardComponent,
    SubmissionAutoTestsViewComponent,
    PopupComponent,
    PopupRefComponent,
    PopupContentComponent,
    DailySubmissionChartComponent,
    AutoTestConclusionSummaryChartsComponent,
    ChartComponent,
    CodeHighlightComponent,
    FileDiffLabelComponent,
    HalloweenPumpkinComponent,
    SpecialDateCardComponent,
    AprilFoolBoxComponent,
    SubmissionCommentsViewComponent,
    CommentsComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  bootstrap: [AppComponent]
})
export class AppModule {
}
