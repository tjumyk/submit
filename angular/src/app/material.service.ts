import {Injectable} from '@angular/core';
import {Observable} from "rxjs";
import {HttpClient} from "@angular/common/http";
import {NotebookPreview} from "./models";

@Injectable({
  providedIn: 'root'
})
export class MaterialService {
  private api = 'api/materials';

  constructor(
    private http: HttpClient
  ) {
  }

  getNotebooks(mid: number): Observable<NotebookPreview[]> {
    return this.http.get<NotebookPreview[]>(`${this.api}/${mid}/notebooks`)
  }
}
