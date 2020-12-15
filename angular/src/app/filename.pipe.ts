import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'filename'
})
export class FilenamePipe implements PipeTransform {
  readonly INVALID_PATTERN = /[\\/:"*?<>|]+/g;
  readonly NORMALIZE_PATTERN = /\s/g;

  transform(value: any, args?: any): any {
    if(!value)
      return '';

    return value.replace(this.INVALID_PATTERN, '').replace(this.NORMALIZE_PATTERN, '_');
  }

}
