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
  user_associations?: UserCourseAssociation[];
  group_associations?: GroupCourseAssociation[];
}

export class Term {
  id: number;
  course_id: number;
  course?: Course;

  year: number;
  semester: string;

  tasks?: Task[];
  user_associations?: UserTermAssociation[];
  group_associations?: GroupTermAssociation[];
}

export class Task {
  id: number;
  type: string;
  title: string;
}

export class Team {
  id: number;
  term_id: number;
  name: string;

  user_associations?: UserTeamAssociation[];
}

export class UserCourseAssociation {
  user_id: number;
  course_id: number;
  role: string;

  user?: User;
  course?: Course;
}

export class GroupCourseAssociation {
  group_id: number;
  course_id: number;
  role: string;

  group?: Group;
  course?: Course;
}

export class UserTermAssociation {
  user_id: number;
  term_id: number;
  role: string;

  user?: User;
  term?: Term;
}

export class GroupTermAssociation {
  group_id: number;
  term_id: number;
  role: string;

  group?: Group;
  term?: Term;
}

export class UserTeamAssociation {
  user_id: number;
  team_id: number;

  user?: User;
  team?: Team;
}
