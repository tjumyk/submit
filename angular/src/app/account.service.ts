import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {tap} from "rxjs/operators";
import {Logger, LogService} from "./log.service";
import {Observable} from "rxjs/internal/Observable";
import {User} from "./models";
import {of} from "rxjs/internal/observable/of";

@Injectable({
  providedIn: 'root'
})
export class AccountService {
  private api: string = 'api/account';
  private logger: Logger;
  private user: User;

  constructor(
    private http: HttpClient,
    logService: LogService
  ) {
    this.logger = logService.get_logger('AccountService')
  }

  static isAdmin(user:User): boolean{
    for(let group of user.groups){
      if(group.name == 'admin')
        return true;
    }
    return false;
  }

  getCurrentUser(): Observable<User> {
    if (this.user)
      return of(this.user);

    return this.http.get<User>(`${this.api}/me`).pipe(
      tap(user => {
        // this.logger.info(`Fetched user info of ${user.name}`);
        this.user = user;
      })
    )
  }

  getUser(id: number): Observable<User>{
    return this.http.get<User>(`${this.api}/users/${id}`)
  }
}
