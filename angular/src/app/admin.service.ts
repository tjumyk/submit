import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable} from "rxjs/internal/Observable";
import {Course, Group, Term} from "./models";
import {Logger, LogService} from "./log.service";
import {tap} from "rxjs/operators";

export class NewCourseForm {
  code: string;
  name: string;
}

export class NewTermForm{
  year: number;
  semester: string;
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

  deleteCourse(cid: number): Observable<any> {
    return this.http.delete(`${this.api}/courses/${cid}`).pipe(
      tap(() => this.logger.info(`Deleted course (id: ${cid})`))
    )
  }

  getCourse(cid: number): Observable<Course> {
    return this.http.get<Course>(`${this.api}/courses/${cid}`).pipe(
      tap((term) => this.logger.info(`Fetched info of course "${term.code}"`))
    )
  }

  updateCourseIcon(cid: number, iconFile: File) {
    const form = new FormData();
    form.append('icon', iconFile);
    return this.http.put<Course>(`${this.api}/courses/${cid}`, form).pipe(
      tap(term => this.logger.info(`Updated icon of course ${term.code}`))
    )
  }

  getTerm(tid: number): Observable<Term>{
    return this.http.get<Term>(`${this.api}/terms/${tid}`).pipe(
      tap(term=>this.logger.info(`Fetched info of term "${term.course.code} - ${term.year}S${term.semester}"`))
    )
  }

  addTerm(courseId: number, form:NewTermForm): Observable<Term>{
    return this.http.post<Term>(`${this.api}/courses/${courseId}/terms`, form).pipe(
      tap(term=>this.logger.info(`Added new term "${term.year}S${term.semester}" to course (course id: ${courseId})`))
    )
  }

  deleteTerm(tid: number): Observable<any> {
    return this.http.delete(`${this.api}/terms/${tid}`).pipe(
      tap(() => this.logger.info(`Deleted term (id: ${tid})`))
    )
  }

  searchGroupsByName(name: string, limit?: number): Observable<Group[]> {
    let params = new HttpParams().append('name', name);
    if(limit != undefined && limit != null)
      params = params.append('limit', limit.toString());
    return this.http.get<Group[]>(`api/oauth-proxy/admin/groups`, {params: params}).pipe(
      tap(results=>this.logger.info(`Search groups by name "${name}", returned ${results.length} results`))
    )
  }
}
