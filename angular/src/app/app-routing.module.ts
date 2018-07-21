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

const routes: Routes = [
  {path: '', pathMatch: 'full', component: HomeComponent},
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
      {path: 'terms/:team_id', component: AdminTermEditComponent}
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
