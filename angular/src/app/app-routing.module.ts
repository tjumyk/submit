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

const routes: Routes = [
  {path: '', pathMatch: 'full', component: HomeComponent},
  {
    path: 'terms/:term_id',
    component: TermComponent,
    children: [
      {path: '', pathMatch: 'full', redirectTo: 'tasks'},
      {path: 'tasks', pathMatch: 'full', component: TasksComponent},
      {
        path: 'tasks/:task_id',
        component: TaskComponent,
        children:[
          {path: '', pathMatch: 'full', redirectTo: 'details'},
          {path: 'details', component: TaskDetailsComponent},
          {path: 'submit', component: SubmitComponent},
          {path: 'my-submissions', component: MySubmissionsComponent},
          {path: 'submissions', component: SubmissionsComponent},
        ]
      },
      {path: 'teams', pathMatch: 'full', component: TeamsComponent},
      {path: 'teams/:team_id', component: TeamComponent}
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
  {path: 'forbidden', component: ForbiddenComponent},
  {path: '**', component: NotFoundComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
