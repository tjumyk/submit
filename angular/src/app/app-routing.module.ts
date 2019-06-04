import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {HomeComponent} from "./home/home.component";
import {AdminComponent} from "./admin/admin.component";
import {AdminGuard} from "./admin.guard";
import {AdminTermEditComponent} from "./admin-term-edit/admin-term-edit.component";
import {ForbiddenComponent} from "./forbidden/forbidden.component";
import {NotFoundComponent} from "./not-found/not-found.component";
import {AdminCoursesComponent} from "./admin-courses/admin-courses.component";
import {AdminCourseNewComponent} from "./admin-course-new/admin-course-new.component";
import {AdminCourseEditComponent} from "./admin-course-edit/admin-course-edit.component";
import {AdminAccountsComponent} from "./admin-accounts/admin-accounts.component";
import {TaskComponent} from "./task/task.component";
import {AdminTaskEditComponent} from "./admin-task-edit/admin-task-edit.component";
import {TermComponent} from "./term/term.component";
import {TeamsComponent} from "./teams/teams.component";
import {TeamComponent} from "./team/team.component";
import {TasksComponent} from "./tasks/tasks.component";
import {SubmitComponent} from "./submit/submit.component";
import {TaskDetailsComponent} from "./task-details/task-details.component";
import {SubmissionsComponent} from "./submissions/submissions.component";
import {MySubmissionsComponent} from "./my-submissions/my-submissions.component";
import {MySubmissionDetailsComponent} from "./my-submission-details/my-submission-details.component";
import {SubmissionDetailsComponent} from "./submission-details/submission-details.component";
import {MyTeamComponent} from "./my-team/my-team.component";
import {MyTeamSubmissionsComponent} from "./my-team-submissions/my-team-submissions.component";
import {MyTeamSubmissionDetailsComponent} from "./my-team-submission-details/my-team-submission-details.component";
import {SubmissionListComponent} from "./submission-list/submission-list.component";
import {TeamSubmissionsComponent} from "./team-submissions/team-submissions.component";
import {TeamSubmissionListComponent} from "./team-submission-list/team-submission-list.component";
import {TeamSubmissionDetailsComponent} from "./team-submission-details/team-submission-details.component";
import {JoinOrCreateTeamComponent} from "./join-or-create-team/join-or-create-team.component";
import {TaskPreviewComponent} from "./task-preview/task-preview.component";
import {TaskDetailsPreviewComponent} from "./task-details-preview/task-details-preview.component";
import {MessagesComponent} from "./messages/messages.component";
import {HelpComponent} from "./help/help.component";
import {AboutComponent} from "./about/about.component";
import {MessageDetailComponent} from "./message-detail/message-detail.component";
import {EmailSubscriptionsComponent} from "./email-subscriptions/email-subscriptions.component";

const routes: Routes = [
  {path: '', pathMatch: 'full', component: HomeComponent},
  {
    path: 'terms/:term_id',
    component: TermComponent,
    children: [
      {path: '', pathMatch: 'full', redirectTo: 'tasks'},
      {path: 'tasks', pathMatch: 'full', component: TasksComponent},
      {
        path: 'tasks-preview/:task_id',
        component: TaskPreviewComponent,
        children: [
          {path: '', pathMatch: 'full', redirectTo: 'details'},
          {path: 'details', component: TaskDetailsPreviewComponent},
          {path: 'my-team', component: MyTeamComponent},
          {path: 'my-team/join-or-create', component: JoinOrCreateTeamComponent},
        ]
      },
      {
        path: 'tasks/:task_id',
        component: TaskComponent,
        children: [
          {path: '', pathMatch: 'full', redirectTo: 'details'},
          {path: 'details', component: TaskDetailsComponent},
          {path: 'submit', component: SubmitComponent},
          {path: 'my-submissions', component: MySubmissionsComponent},
          {path: 'my-submissions/:submission_id', component: MySubmissionDetailsComponent},
          {path: 'my-team-submissions', component: MyTeamSubmissionsComponent},
          {path: 'my-team-submissions/:submission_id', component: MyTeamSubmissionDetailsComponent},
          {path: 'user-submissions', component: SubmissionsComponent},
          {path: 'user-submissions/:user_id', component: SubmissionListComponent},
          {path: 'user-submissions/:user_id/:submission_id', component: SubmissionDetailsComponent},
          {path: 'team-submissions', component: TeamSubmissionsComponent},
          {path: 'team-submissions/:team_id', component: TeamSubmissionListComponent},
          {path: 'team-submissions/:team_id/:submission_id', component: TeamSubmissionDetailsComponent},
          {path: 'my-team', component: MyTeamComponent},
          {path: 'my-team/join-or-create', component: JoinOrCreateTeamComponent},
          {path: 'teams', component: TeamsComponent},
          {path: 'teams/:team_id', component: TeamComponent}
        ]
      },
      {path: 'messages', component: MessagesComponent},
      {path: 'messages/:msg_id', component: MessageDetailComponent}
    ]
  },
  {
    path: 'admin',
    component: AdminComponent,
    canActivate: [AdminGuard],
    children: [
      {path: '', pathMatch: 'full', redirectTo: 'courses'},
      {path: 'accounts', component: AdminAccountsComponent},
      {path: 'courses', component: AdminCoursesComponent},
      {path: 'new-course', component: AdminCourseNewComponent},
      {path: 'courses/:course_id', component: AdminCourseEditComponent},
      {path: 'terms/:team_id', component: AdminTermEditComponent},
      {path: 'tasks/:task_id', component: AdminTaskEditComponent},
    ]
  },
  {path: 'email-subscriptions', component: EmailSubscriptionsComponent},
  {path: 'help', component: HelpComponent},
  {path: 'about', component: AboutComponent},
  {path: 'forbidden', component: ForbiddenComponent},
  {path: '**', component: NotFoundComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
