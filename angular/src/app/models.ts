export class Message {
  msg: string;
  detail?: string;
}

export class SuccessMessage extends Message {
}

export class ErrorMessage extends Message {
}

export class User {
  id: number;
  name: string;
  email: string;
  nickname: string;
  avatar: string;

  groups: Group[];
}

export class Group {
  id: number;
  name: string;
  description: string;
}

export class Course {
  id: number;
  code: string;
  name: string;

  terms?: Term[];
}

export class Term {
  id: number;
  course_id: number;
  course?: Course;

  year: number;
  semester: string;

  tasks?: Task[];
}

export class Task {
  id: number;
  type: string;
  title: string;
}
