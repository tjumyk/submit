import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable} from "rxjs";
import {AutoTest, AutoTestConfig, AutoTestList, Submission, SubmissionComment, SubmissionFileDiff} from "./models";

export class AutoTestConfigTypeInfo {
  id: string;
  name: string;
  icon: string;
}

@Injectable({
  providedIn: 'root'
})
export class SubmissionService {
  readonly api = 'api/submissions';
  readonly myApi = 'api/my-submissions';
  readonly myTeamApi = 'api/my-team-submissions';

  autoTestConfigTypes: {[id: string]: AutoTestConfigTypeInfo} = {
    'docker': {
      id: 'docker',
      name: 'Docker',
      icon: 'docker'
    },
    'run-script': {
      id: 'run-script',
      name: 'Run Script',
      icon: 'terminal'
    },
    'anti-plagiarism': {
      id: 'anti-plagiarism',
      name: 'Anti Plagiarism',
      icon: 'copyright'
    },
    'file-exists': {
      id: 'file-exists',
      name: 'File Exists',
      icon: 'file outline'
    }
  };

  constructor(
    private http: HttpClient
  ) {
  }

  getSubmission(id: number, apiBase: string = this.api): Observable<Submission> {
    return this.http.get<Submission>(`${apiBase}/${id}`)
  }

  getMySubmission(id: number): Observable<Submission> {
    return this.getSubmission(id, this.myApi)
  }

  getMyTeamSubmission(id: number): Observable<Submission> {
    return this.getSubmission(id, this.myTeamApi)
  }

  getAutoTestAndResults(id: number, apiBase: string=this.api,
                        updateAfterTimestamp: number=undefined): Observable<AutoTestList> {
    let params = new HttpParams();
    if(updateAfterTimestamp)
      params = params.append('update_after', `${updateAfterTimestamp}`);
    return this.http.get<AutoTestList>(`${apiBase}/${id}/auto-tests`, {params})
  }

  getDiffs(id:number, apiBase: string=this.api):Observable<{[fid:number]: SubmissionFileDiff}>{
    return this.http.get<{[fid:number]: SubmissionFileDiff}>(`${apiBase}/${id}/diff`)
  }

  getComments(sid: number, apiBase: string = this.api): Observable<SubmissionComment[]> {
    return this.http.get<SubmissionComment[]>(`${apiBase}/${sid}/comments`)
  }

  addComment(sid: number, content: string, apiBase: string = this.api): Observable<SubmissionComment> {
    return this.http.post<SubmissionComment>(`${apiBase}/${sid}/comments`, {content})
  }

  updateComment(sid: number, cid: number, content: string, apiBase: string = this.api): Observable<SubmissionComment> {
    return this.http.put<SubmissionComment>(`${apiBase}/${sid}/comments/${cid}`, {content})
  }

  removeComment(sid: number, cid: number, apiBase: string = this.api): Observable<any> {
    return this.http.delete(`${apiBase}/${sid}/comments/${cid}`)
  }

  getAutoTestStatusColor(status: string): string {
    switch (status) {
      case 'STARTED':
        return '#2185d0';
      case 'SUCCESS':
        return '#21ba45';
      case 'RETRY':
        return '#fbbd08';
      case 'FAILURE':
        return '#db2828';
      case 'REVOKED':
        return '#db2828';
      case 'PENDING':
        return '#767676';
      default:
        return '#1b1c1d';
    }
  }

  getAutoTestStatusClass(status: string): string {
    switch (status) {
      case 'STARTED':
        return 'blue';
      case 'SUCCESS':
        return 'green';
      case 'RETRY':
        return 'yellow';
      case 'FAILURE':
        return 'red';
      case 'REVOKED':
        return 'red';
      case 'PENDING':
        return 'grey';
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

  extractConclusion(test: AutoTest, config: AutoTestConfig) {
    if (!test)
      return null;
    if (!config)
      return null;

    return this.evaluateObjectPath(test.result, config.result_conclusion_path);
  };

  printConclusion(test: AutoTest, config: AutoTestConfig) {
    if (!test)
      return null;
    if (!config)
      return null;

    let conclusion = this.extractConclusion(test, config);

    if (config.result_conclusion_type == 'json')
      conclusion = JSON.stringify(conclusion);
    return conclusion;
  };

  renderResultHTML(test: AutoTest, config: AutoTestConfig): string {
    if (!test)
      return '';
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
        case 'percent':
          if (typeof result == 'number')
            result = Math.round(result * 100) + '%';
          break
      }
      if (result === null || result === undefined)
        return '';
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
