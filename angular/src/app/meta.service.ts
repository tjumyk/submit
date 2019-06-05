import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {QAndA, VersionInfo} from "./models";

@Injectable({
  providedIn: 'root'
})
export class MetaService {
  private api = 'api/meta';

  constructor(
    private http: HttpClient
  ) { }

  getVersion():Observable<VersionInfo>{
    return this.http.get<VersionInfo>(`${this.api}/version`)
  }

  getFAQ():Observable<QAndA[]>{
    return this.http.get<QAndA[]>(`${this.api}/faq`)
  }
}
