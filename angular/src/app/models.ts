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
  team_associations?: UserTeamAssociation[];
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

  icon?: string;
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
  late_penalty?: string;

  is_team_task: boolean;
  team_min_size?: number;
  team_max_size?: number;
  team_join_close_time?: string;
  submission_attempt_limit?: number;
  submission_history_limit?: number;

  evaluation_method?: string;
  auto_test_trigger?: string;
  auto_test_environment_id?: number;

  created_at: string;
  modified_at: string;

  term?: Term;
  materials?: Material[];
  file_requirements?: FileRequirement[];
  special_considerations?: SpecialConsideration[];
}

export class Material {
  id: number;
  task_id: number;

  type: string;
  name: string;
  is_private: boolean;
  description?: string;

  created_at: string;
  modified_at: string;

  file_path: string;
  size?: number;
  md5?: string;
}

export class FileRequirement {
  id: number;
  task_id: number;

  name: string;
  description?: string;
  is_optional: boolean;
  size_limit?: number;

  created_at: string;
  modified_at: string;
}

export class Submission {
  id: number;
  task_id: number;
  submitter_id: number;
  is_cleared: boolean;
  files: SubmissionFile[];

  task?: Task;
  submitter?: User;

  created_at: string;
  modified_at: string;
}

export class SubmissionFile {
  id: number;
  submission_id: number;
  requirement_id: number;

  submission?: Submission;
  requirement?: FileRequirement;
  path: string;
  size?: number;
  md5?: string;

  created_at: string;
  modified_at: string;
}

export class Team {
  id: number;
  task_id: number;
  creator_id: number;

  name: string;
  is_finalised: boolean;
  slogan?: string;

  created_at: string;
  modified_at: string;

  task?: Task;
  creator?: User;
  submissions?: Submission[];
  user_associations?: UserTeamAssociation[];

  // client-side injected attributes
  total_user_associations: number;
}


export class UserTeamAssociation {
  user_id: number;
  team_id: number;

  is_invited: boolean;
  is_user_agreed: boolean;
  is_creator_agreed: boolean;

  created_at: string;
  modified_at: string;

  user?: User;
  team?: Team;
}

export class UserSubmissionSummary {
  user: User;
  total_submissions: number;
  last_submit_time: string;
}

export class TeamSubmissionSummary {
  team: Team;
  total_submissions: number;
  last_submit_time: string;
}


export class SpecialConsideration {
  id: number;
  task_id: number;

  user_id?: number;
  team_id?: number;

  due_time_extension?: number;
  submission_attempt_limit_extension?: number;

  created_at: string;
  modified_at: string;

  task?: Task;
  user?: User;
  team?: Team;
}

export class SubmissionStatus {
  attempts: number;
  team_association?: UserTeamAssociation;
  special_consideration?: SpecialConsideration;
}

export class AutoTest {
  id: number;
  submission_id: number;

  work_id: string;

  hostname?: string;
  pid?: number;

  state: string;
  final_state?: string;
  result?: any;
  exception_class: string;
  exception_message: string;
  exception_traceback: string;

  created_at: string;
  modified_at: string;
  started_at: string;
  stopped_at: string;

  submission?: Submission;
  output_files?: AutoTestOutputFile[];
}

export class AutoTestOutputFile {
  id: number;
  auto_test_id: number;

  path: string;
  save_path: string;

  created_at: string;
  modified_at: string;

  auto_test?: AutoTest;
}
