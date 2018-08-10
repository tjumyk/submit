import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {Course} from "./models";
import {tap} from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class CourseService {
  private api:string = 'api/courses';

  constructor(
    private http:HttpClient
  ) { }

  getCourses():Observable<Course[]>{
    return this.http.get<Course[]>(`${this.api}`).pipe(
      tap(courses=>{
        for(let course of courses){
          for(let term of course.terms){
            term.course = course;
          }
        }
      })
    )
  }
}
