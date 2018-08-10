import { Pipe, PipeTransform } from '@angular/core';
import {isNumber} from "util";

@Pipe({
  name: 'size'
})
export class SizePipe implements PipeTransform {

  private units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  transform(value: any, args?: any): string {
    if(value == null || value == undefined)
      return '';
    if(!isNumber(value))
      return 'NaN';
    let remain = value;
    let unitIndex = 0;
    while (remain >= 1024 && unitIndex < this.units.length - 1) {
      remain /= 1024;
      unitIndex++;
    }
    return `${remain.toFixed(1)} ${this.units[unitIndex]}`;
  }

}
