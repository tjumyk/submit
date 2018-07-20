import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { AdminComponent } from './admin/admin.component';
import { AdminTermEditComponent } from './admin-term-edit/admin-term-edit.component';
import {HttpClientModule} from "@angular/common/http";
import {FormsModule} from "@angular/forms";
import { HomeComponent } from './home/home.component';
import {ForbiddenComponent} from "./forbidden/forbidden.component";
import {NotFoundComponent} from "./not-found/not-found.component";
import { ErrorMessageComponent } from './error-message/error-message.component';
import { AdminCoursesComponent } from './admin-courses/admin-courses.component';
import { AdminCourseEditComponent } from './admin-course-edit/admin-course-edit.component';
import { AdminCourseNewComponent } from './admin-course-new/admin-course-new.component';
import { SuccessMessageComponent } from './success-message/success-message.component';

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
    SuccessMessageComponent
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
export class AppModule { }
