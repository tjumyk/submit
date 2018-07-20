export class SuccessMessage {
  msg: string;
  detail?: string;
}

export class ErrorMessage {
  msg: string;
  detail?: string;
}

export class User{
  id: number;
  name: string;
  email: string;
  nickname: string;
  avatar: string;

  groups: Group[];
}

export class Group{
  id: number;
  name: string;
  description: string;
}

export class Course{
  id: number;
  code: string;
  name: string;
}

export class Term{
  id: number;
  course_id: number;
  course?: Course;

  year: number;
  semester: string;
}
