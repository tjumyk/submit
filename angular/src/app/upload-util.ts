import {ErrorMessage} from "./models";

export class UploadFilter {
  readonly accept: string[];
  readonly accept_ext: string[];
  readonly size_limit: number
}

export class UploadFilters {
  static avatar: UploadFilter = {
    "accept": ["image/png", "image/jpg", "image/jpeg", "image/gif"],
    "accept_ext": ["png", "jpg", "jpeg", "gif"],
    "size_limit": 262144,

  };

  static icon: UploadFilter = {
    "accept": ["image/png", "image/jpg", "image/jpeg", "image/gif", "image/svg+xml"],
    "accept_ext": ["png", "jpg", "jpeg", "gif", "svg"],
    "size_limit": 262144
  };
}

export class UploadValidator {
  error: ErrorMessage;

  constructor(readonly filter: UploadFilter) {
  }

  check(file: File): boolean {
    this.error = undefined;

    if (!file) {
      this.error = {msg:'no file', detail:undefined};
      return false;
    }

    if(this.filter.accept_ext){
      let accepted = false;
      const ext = file.name.split('.').pop();
      for(let accept_ext of this.filter.accept_ext){
        if(accept_ext == ext){
          accepted = true;
          break
        }
      }
      if(!accepted){
        this.error = {msg: 'invalid file extension', detail: undefined};
        return false;
      }
    }

    if (file.size > this.filter.size_limit) {
      this.error = {msg:'size too big', detail:`File '${file.name}' has ${Math.round(file.size/1024)} KB`};
      return false;
    }

    return true
  }
}

