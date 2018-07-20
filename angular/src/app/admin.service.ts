import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs/internal/Observable";
import {Course} from "./models";
import {Logger, LogService} from "./log.service";
import {tap} from "rxjs/operators";

export class NewCourseForm{
  code: string;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private api: string = 'api/admin';
  private logger: Logger;

  constructor(
    private http: HttpClient,
    private logService: LogService
  ) {
    this.logger = this.logService.get_logger('AdminService')
  }

  getCourses(): Observable<Course[]> {
    return this.http.get<Course[]>(`${this.api}/courses`).pipe(
      tap((courses) => this.logger.info(`Fetched course list (${courses.length} courses)`))
    )
  }

  addCourse(form: NewCourseForm): Observable<Course> {
    return this.http.post<Course>(`${this.api}/courses`, form).pipe(
      tap((term: Course) => this.logger.info(`Added new course "${term.code}"`))
    )
  }

  deleteCourse(tid: number):Observable<any> {
    return this.http.delete(`${this.api}/courses/${tid}`).pipe(
      tap(()=>this.logger.info(`Deleted course (id: ${tid})`))
    )
  }

  getCourse(tid: number):Observable<Course> {
    return this.http.get<Course>(`${this.api}/courses/${tid}`).pipe(
      tap((term)=>this.logger.info(`Fetched info of course "${term.code}"`))
    )
  }

  updateCourseIcon(tid: number, iconFile: File){
    const form = new FormData();
    form.append('icon', iconFile);
    return this.http.put<Course>(`${this.api}/courses/${tid}`, form).pipe(
      tap(term=>this.logger.info(`Updated icon of course ${term.code}`))
    )
  }

}
