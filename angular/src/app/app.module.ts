import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

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
import {AdminTeamsComponent} from './admin-teams/admin-teams.component';
import {TermComponent} from './term/term.component';
import {TaskComponent} from './task/task.component';
import {TeamComponent} from './team/team.component';
import {SubmitComponent} from './submit/submit.component';
import {AdminSubmissionsComponent} from './admin-submissions/admin-submissions.component';
import {AdminSubmissionComponent} from './admin-submission/admin-submission.component';
import {TeamsComponent} from './teams/teams.component';
import {AdminTeamComponent} from './admin-team/admin-team.component';
import {SizePipe} from './size.pipe';
import {TasksComponent} from './tasks/tasks.component';
import {TaskDetailsComponent} from './task-details/task-details.component';
import {SubmissionsComponent} from './submissions/submissions.component';
import {MySubmissionsComponent} from './my-submissions/my-submissions.component';
import { MySubmissionDetailsComponent } from './my-submission-details/my-submission-details.component';
import { SubmissionDetailsComponent } from './submission-details/submission-details.component';
import { MyTeamComponent } from './my-team/my-team.component';
import { MyTeamSubmissionsComponent } from './my-team-submissions/my-team-submissions.component';
import { MyTeamSubmissionDetailsComponent } from './my-team-submission-details/my-team-submission-details.component';
import { TeamSubmissionsComponent } from './team-submissions/team-submissions.component';
import { TeamSubmissionDetailsComponent } from './team-submission-details/team-submission-details.component';
import { SubmissionListComponent } from './submission-list/submission-list.component';
import { TeamSubmissionListComponent } from './team-submission-list/team-submission-list.component';
import { JoinOrCreateTeamComponent } from './join-or-create-team/join-or-create-team.component';

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
    AdminTeamsComponent,
    TermComponent,
    TaskComponent,
    TeamComponent,
    SubmitComponent,
    AdminSubmissionsComponent,
    AdminSubmissionComponent,
    TeamsComponent,
    AdminTeamComponent,
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
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {
}
