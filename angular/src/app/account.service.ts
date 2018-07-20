import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {tap} from "rxjs/operators";
import {Logger, LogService} from "./log.service";
import {Observable} from "rxjs/internal/Observable";
import {User} from "./models";

@Injectable({
  providedIn: 'root'
})
export class AccountService {
  private api: string = 'api/account';
  private logger: Logger;

  constructor(
    private http: HttpClient,
    logService: LogService
  ) {
    this.logger = logService.get_logger('AccountService')
  }

  get_current_user(): Observable<User> {
    return this.http.get<User>('/api/account/me').pipe(
      tap(user => this.logger.info(`Fetched user info of ${user.name}`))
    )
  }
}
