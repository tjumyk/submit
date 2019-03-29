import {Injectable} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {AutoTest, AutoTestConfig, Submission} from "./models";

@Injectable({
  providedIn: 'root'
})
export class SubmissionService {
  private api = 'api/submissions';
  private myApi = 'api/my-submissions';
  private myTeamApi = 'api/my-team-submissions';

  constructor(
    private http: HttpClient
  ) {
  }

  getSubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.api}/${id}`)
  }

  getMySubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.myApi}/${id}`)
  }

  getMyTeamSubmission(id: number): Observable<Submission> {
    return this.http.get<Submission>(`${this.myTeamApi}/${id}`)
  }

  getAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.api}/${id}/auto-tests`)
  }

  getMyAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.myApi}/${id}/auto-tests`)
  }

  getMyTeamAutoTestAndResults(id: number): Observable<AutoTest[]> {
    return this.http.get<AutoTest[]>(`${this.myTeamApi}/${id}/auto-tests`)
  }

  getAutoTestStatusColor(status: string): string {
    switch (status) {
      case 'STARTED':
        return '#21ba45';
      case 'SUCCESS':
        return '#21ba45';
      case 'RETRY':
        return '#fbbd08';
      case 'FAILURE':
        return '#db2828';
      case 'REVOKED':
        return '#db2828';
      default:
        return '#1b1c1d';
    }
  }

  getAutoTestStatusClass(status: string): string {
    switch (status) {
      case 'STARTED':
        return 'green';
      case 'SUCCESS':
        return 'green';
      case 'RETRY':
        return 'yellow';
      case 'FAILURE':
        return 'red';
      case 'REVOKED':
        return 'red';
      default:
        return 'black';
    }
  }

  /* Utility for AutoTests */
  evaluateObjectPath(obj, path: string) {
    let ret = obj;
    if (path) {
      for (let segment of path.split('.')) {
        if (!segment)
          return null; // unexpected empty segment
        if (typeof ret != 'object')
          return null;
        ret = ret[segment]
      }
    }
    return ret;
  };

  extractConclusion(test: AutoTest, config?: AutoTestConfig) {
    if (!test)
      return null;
    if (!config)
      config = test.config;
    if (!config)
      return null;

    return this.evaluateObjectPath(test.result, config.result_conclusion_path);
  };

  printConclusion(test: AutoTest, config?: AutoTestConfig) {
    if (!test)
      return null;
    if (!config)
      config = test.config;
    if (!config)
      return null;

    let conclusion = this.extractConclusion(test, config);

    if (config.result_conclusion_type == 'json')
      conclusion = JSON.stringify(conclusion);
    return conclusion;
  };

  renderResultHTML(test: AutoTest, config?: AutoTestConfig): string {
    if (!test)
      return '';
    if (!config)
      config = test.config;
    if (!config)
      return '';

    let html = config.result_render_html;
    html = html.replace(/{{([^}]*)}}/g, (match, expr: string) => {
      let parts = expr.trim().split('|', 2);
      let path = parts[0].trim();
      let pipe = null;
      if (parts.length > 1)
        pipe = parts[1].trim();

      let result = this.evaluateObjectPath(test.result, path);
      switch (pipe) {
        case 'json':
          result = JSON.stringify(result, null, 2);
          break;
      }
      return SubmissionService.escapeHtml(result.toString())
    });
    return html;
  }

  static escapeHtml(unsafe) {
    // https://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}
