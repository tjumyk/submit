import {Injectable} from '@angular/core';
import {ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot} from '@angular/router';
import {Observable} from 'rxjs';
import {AccountService} from "./account.service";
import {catchError, map} from "rxjs/operators";
import {of} from "rxjs/internal/observable/of";
import {Logger, LogService} from "./log.service";
import {User} from "./models";

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {
  private logger: Logger;

  constructor(
    private accountService: AccountService,
    private router: Router,
    private logService: LogService
  ) {
    this.logger = logService.get_logger('AdminGuard')
  }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {
    return this.accountService.getCurrentUser().pipe(
      map((user: User) => {
        if (user != null) {
          for (let group of user.groups) {
            if (group.name == 'admin') {
              this.logger.info('Admin verified');
              return true;
            }
          }
        }
        this.router.navigate(['/forbidden']);
        this.logger.warn('Not admin');
        return false;
      }),
      catchError((error) => {
        const redirect_url = error.error.redirect_url;
        if (redirect_url) {
          this.logger.warn('OAuth session closed. Redirect required');
          window.location.href = redirect_url;
        } else {
          this.logger.error(`Failed to get user info: ${error.error.msg}`);
          this.router.navigate(['/forbidden']);
        }
        return of(false);
      })
    )
  }
}
