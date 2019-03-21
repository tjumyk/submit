import {Injectable} from '@angular/core';
import {HttpClient, HttpEvent, HttpParams, HttpRequest} from "@angular/common/http";
import {Observable} from "rxjs/internal/Observable";
import {
  AutoTest, AutoTestConfig,
  Course,
  ErrorMessage,
  FileRequirement,
  Group,
  Material,
  SpecialConsideration,
  Task,
  Term,
  User
} from "./models";
import {Logger, LogService} from "./log.service";
import {map, tap} from "rxjs/operators";
import * as moment from"moment";

export class NewCourseForm {
  code: string;
  name: string;
  tutor_group_name: string;
  is_new_tutor_group: boolean;
}

export class NewTermForm {
  year: number;
  semester: string;
  student_group_name: string;
  is_new_student_group: boolean;
}

export class NewTaskForm{
  type: string;
  title: string;
  description?: string;
}

export class UpdateTaskForm{
  type: string;
  title: string;
  description?: string;
  open_time?: string;
  due_time?: string;
  close_time? : string;
  late_penalty?: string;
  is_team_task: boolean;
  team_min_size?: number;
  team_max_size?: number;
  team_join_close_time?: string;
  submission_attempt_limit?: number;
  submission_history_limit?: number;
  evaluation_method?: string;
}

export class NewMaterialForm{
  type: string;
  name: string;
  description?: string;
  is_private: boolean;
}

export class UpdateMaterialForm{
  description: string;
  is_private: boolean;
}

export class NewFileRequirementForm{
  name: string;
  is_optional: boolean;
  size_limit?:number;
  description?:string;
}

export class NewAutoTestConfigForm{
  name: string;
  type: string;
  environment_id?: number;
  description?: string;
  is_enabled: boolean;
  is_private: boolean;
}

export class UpdateAutoTestConfigForm{
  name: string;
  type: string;
  description?: string;
  is_enabled: boolean;
  is_private: boolean;

  priority: number;
  trigger?: string;
  environment_id?: number;
  docker_auto_remove: boolean;
  docker_cpus?: number;
  docker_memory?: number;
  docker_network: boolean;

  result_render_html?: string;
  result_conclusion_type: string;
  result_conclusion_path?: string;
  results_conclusion_accumulate_method: string;
}

export class NewSpecialConsiderationForm{
  user_name?: number;
  team_name?:number;
  due_time_extension?: number;
  submission_attempt_limit_extension?: number;
}

export class TestEnvironmentValidationResult{
  type?: string;
  conda_version?: string;
  docker_entry_point?: string;
  docker_cmd?: string;
  docker_run_config?: {};
  pip_requirements?: string[];
  error?: ErrorMessage;
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


  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.api}/users`).pipe(
      map((data) => {
        let group_dict: { [gid: number]: Group } = {};
        for (let group  of data['groups']) {
          let g = group as Group;
          group_dict[g.id] = g
        }
        let users: User[] = [];
        for (let user of data['users']) {
          let groups = [];
          for (let gid of user['group_ids']) {
            groups.push(group_dict[gid])
          }
          user['groups'] = groups;
          let u = user as User;
          users.push(u)
        }
        return users
      }),
      tap((courses) => this.logger.info(`Fetched user list (${courses.length} users)`))
    )
  }

  searchUsersByName(name: string, limit?: number): Observable<User[]> {
    let params = new HttpParams().append('name', name);
    if (limit != undefined && limit != null)
      params = params.append('limit', limit.toString());
    return this.http.get<User[]>(`${this.api}/users`, {params: params}).pipe(
      tap(results => this.logger.info(`Search users by name "${name}", returned ${results.length} results`))
    )
  }

  getGroups(): Observable<Group[]> {
    return this.http.get<Group[]>(`${this.api}/groups`).pipe(
      tap((courses) => this.logger.info(`Fetched group list (${courses.length} groups)`))
    )
  }

  searchGroupsByName(name: string, limit?: number): Observable<Group[]> {
    let params = new HttpParams().append('name', name);
    if (limit != undefined && limit != null)
      params = params.append('limit', limit.toString());
    return this.http.get<Group[]>(`${this.api}/groups`, {params: params}).pipe(
      tap(results => this.logger.info(`Search groups by name "${name}", returned ${results.length} results`))
    )
  }

  syncUsers(): Observable<any> {
    return this.http.get(`${this.api}/sync-users`).pipe(
      tap(() => this.logger.info(`Synchronised users`))
    )
  }

  syncGroups(): Observable<any> {
    return this.http.get(`${this.api}/sync-groups`).pipe(
      tap(() => this.logger.info(`Synchronised groups`))
    )
  }

  deleteUser(user_id: number): Observable<any> {
    return this.http.delete(`${this.api}/users/${user_id}`).pipe(
      tap(()=>this.logger.info(`Deleted user alias (id=${user_id})`))
    )
  }

  deleteGroup(group_id: number): Observable<any> {
    return this.http.delete(`${this.api}/groups/${group_id}`).pipe(
      tap(()=>this.logger.info(`Deleted group alias (id=${group_id})`))
    )
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

  getTerm(tid: number): Observable<Term> {
    return this.http.get<Term>(`${this.api}/terms/${tid}`).pipe(
      tap(term => this.logger.info(`Fetched info of term "${term.course.code} - ${term.year}S${term.semester}"`))
    )
  }

  addTerm(courseId: number, form: NewTermForm): Observable<Term> {
    return this.http.post<Term>(`${this.api}/courses/${courseId}/terms`, form).pipe(
      tap(term => this.logger.info(`Added new term "${term.year}S${term.semester}" to course (course id: ${courseId})`))
    )
  }

  deleteTerm(tid: number): Observable<any> {
    return this.http.delete(`${this.api}/terms/${tid}`).pipe(
      tap(() => this.logger.info(`Deleted term (id: ${tid})`))
    )
  }

  getTask(task_id: number): Observable<Task>{
    return this.http.get<Task>(`${this.api}/tasks/${task_id}`)
  }

  addTask(term_id: number, form: NewTaskForm):Observable<Task>{
    return this.http.post<Task>(`${this.api}/terms/${term_id}/tasks`, form)
  }

  updateTask(task_id: number, form: UpdateTaskForm):Observable<Task>{
    const formCopy = {...form};
    // transform naive time strings into ISO strings in UTC
    formCopy.open_time = moment(form.open_time).toISOString();
    formCopy.due_time = moment(form.due_time).toISOString();
    formCopy.close_time = moment(form.close_time).toISOString();
    formCopy.team_join_close_time = moment(form.team_join_close_time).toISOString();
    return this.http.put<Task>(`${this.api}/tasks/${task_id}`, formCopy)
  }

  deleteTask(task_id: number):Observable<any>{
    return this.http.delete(`${this.api}/tasks/${task_id}`)
  }

  addMaterial(task_id: number, form: NewMaterialForm, file: File): Observable<HttpEvent<any>>{
    const data = new FormData();
    data.append('type', form.type);
    data.append('name', form.name);
    data.append('file', file);
    data.append('is_private', form.is_private ? 'true': 'false');
    if(form.description)
      data.append('description', form.description);
    const req = new HttpRequest('POST', `${this.api}/tasks/${task_id}/materials`, data, {reportProgress: true});
    return this.http.request(req);
  }

  updateMaterialFile(material_id: number, file: File): Observable<HttpEvent<any>>{
    const data = new FormData();
    data.append('file', file);
    const req = new HttpRequest('PUT', `${this.api}/materials/${material_id}`, data, {reportProgress: true});
    return this.http.request(req);
  }

  updateMaterial(material_id: number, form: UpdateMaterialForm): Observable<Material>{
    return this.http.put<Material>(`${this.api}/materials/${material_id}`, form);
  }

  deleteMaterial(material_id: number): Observable<any>{
    return this.http.delete(`${this.api}/materials/${material_id}`)
  }

  validateTestEnvironment(material_id: number): Observable<TestEnvironmentValidationResult>{
    return this.http.get(`${this.api}/materials/${material_id}/validate-test-environment`);
  }

  addAutoTestConfig(task_id: number, form: NewAutoTestConfigForm): Observable<AutoTestConfig>{
    return this.http.post<AutoTestConfig>(`${this.api}/tasks/${task_id}/auto-test-configs`, form)
  }

  updateAutoTestConfig(config_id: number, form: UpdateAutoTestConfigForm): Observable<AutoTestConfig>{
    return this.http.put<AutoTestConfig>(`${this.api}/auto-test-configs/${config_id}`, form)
  }

  deleteAutoTestConfig(config_id: number): Observable<any>{
    return this.http.delete(`${this.api}/auto-test-configs/${config_id}`)
  }

  addFileRequirement(task_id: number, form:NewFileRequirementForm):Observable<FileRequirement>{
    return this.http.post<FileRequirement>(`${this.api}/tasks/${task_id}/file-requirements`, form)
  }

  deleteFileRequirement(requirement_id: number):Observable<any>{
    return this.http.delete(`${this.api}/file-requirements/${requirement_id}`)
  }

  addSpecialConsideration(task_id: number, form:NewSpecialConsiderationForm):Observable<SpecialConsideration>{
    return this.http.post<SpecialConsideration>(`${this.api}/tasks/${task_id}/special-considerations`, form)
  }

  deleteSpecialConsiderations(spec_id: number):Observable<any>{
    return this.http.delete(`${this.api}/special-considerations/${spec_id}`)
  }

  deleteTeam(team_id: number):Observable<any>{
    return this.http.delete(`${this.api}/teams/${team_id}`)
  }

  runAutoTest(submission_id: number, config_id: number): Observable<AutoTest> {
    return this.http.get<AutoTest>(`${this.api}/submissions/${submission_id}/run-auto-test/${config_id}`)
  }

  deleteAutoTest(id: number, tid: number): Observable<any> {
    return this.http.delete(`${this.api}/submissions/${id}/auto-tests/${tid}`)
  }

  /* Utility for AutoTests */
  static evaluatePath(obj, path: string){
    let ret = obj;
    if(path){
      for(let segment of path.split('.')){
        if(typeof ret != 'object')
          return null;
        ret = ret[segment]
      }
    }
    return ret;
  }

  static printConclusion(test: AutoTest){
    let config = test.config;
    if(!config)
      return null;

    let conclusion = AdminService.evaluatePath(test.result, config.result_conclusion_path);
    if(config.result_conclusion_type == 'json')
      conclusion = JSON.stringify(conclusion);
    return conclusion;
  }

  static renderResultHTML(test: AutoTest){
    let config = test.config;
    if(!config)
      return '';

    let html = config.result_render_html;
    html = html.replace(/{{([^}]*)}}/g, (match, path)=>{
      return AdminService.evaluatePath(test.result, path)
    });
    return html;
  }
}
