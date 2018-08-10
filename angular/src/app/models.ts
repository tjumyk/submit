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
  team_association?: UserTeamAssociation[];
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
  tutor_group_id: number;

  icon?:string;
  terms?: Term[];
  tutor_group?: Group;
}

export class Term {
  id: number;
  course_id: number;
  course?: Course;
  student_group_id: number;

  year: number;
  semester: string;

  tasks?: Task[];
  student_group?: Group;
}

export class Task {
  id: number;
  term_id: number;

  type: string;
  title: string;
  description?: string;

  open_time?: string;
  due_time?: string;
  close_time?: string;
  late_penalty?: number;

  is_team_task: boolean;
  team_min_size?: number;
  team_max_size?: number;
  submission_limit?: number;
  submission_history_limit?: number;

  created_at: string;
  modified_at: string;

  term?: Term;
  materials?: Material[];
  file_requirements?: FileRequirement[];
}

export class Material{
  id: number;
  task_id: number;

  type: string;
  name: string;
  description?: string;

  created_at: string;
  modified_at: string;

  file_path?: string;
}

export class FileRequirement{
  id: number;
  task_id: number;

  name: string;
  description?: string;
  is_optional: boolean;
  size_limit?: number;

  created_at: string;
  modified_at: string;
}

export class Submission{
  id: number;
  task_id: number;
  submitter_id: number;
  submitter_team_id: number;
  files: SubmissionFile[];

  task?:Task;
  submitter?: User;
  submitter_team?:Team;

  created_at: string;
  modified_at: string;
}

export class SubmissionFile{
  id: number;
  submission_id: number;
  requirement_id: number;

  submission?: Submission;
  requirement?: FileRequirement;
  file_path?: string;

  created_at: string;
  modified_at: string;
}

export class Team {
  id: number;
  term_id: number;
  name: string;

  user_associations?: UserTeamAssociation[];
}


export class UserTeamAssociation {
  user_id: number;
  team_id: number;

  user?: User;
  team?: Team;
}
