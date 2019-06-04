import {Component, OnInit} from '@angular/core';
import {Location} from "@angular/common";
import {HttpClient} from "@angular/common/http";
import {ErrorMessage, VersionInfo} from "../models";
import {MetaService} from "../meta.service";


@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.less']
})
export class AboutComponent implements OnInit {
  error: ErrorMessage;
  version: VersionInfo;

  constructor(
    private location: Location,
    private metaService: MetaService
  ) {
  }

  ngOnInit() {
    this.metaService.getVersion().subscribe(
      version => this.version = version,
      error => this.error = error.error
    )
  }

  navigateBack() {
    this.location.back()
  }
}
