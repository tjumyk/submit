import {Component, OnInit} from '@angular/core';
import {ErrorMessage, FileRequirement, Material, SpecialConsideration, SuccessMessage, Task} from "../models";
import {
  AdminService,
  NewFileRequirementForm,
  NewMaterialForm,
  NewSpecialConsiderationForm,
  UpdateTaskForm
} from "../admin.service";
import {ActivatedRoute} from "@angular/router";
import {finalize} from "rxjs/operators";
import {NgForm} from "@angular/forms";
import * as moment from "moment";
import {HttpEventType} from "@angular/common/http";
import {TaskService} from "../task.service";
import {TitleService} from "../title.service";

@Component({
  selector: 'app-admin-task-edit',
  templateUrl: './admin-task-edit.component.html',
  styleUrls: ['./admin-task-edit.component.less']
})
export class AdminTaskEditComponent implements OnInit {
  success: SuccessMessage;
  error: ErrorMessage;
  secondaryError: ErrorMessage;
  thirdError: ErrorMessage;
  taskId: number;
  task: Task;
  loadingTask: boolean;
  categories = TaskService.categories;

  updating: boolean;
  form: UpdateTaskForm = new UpdateTaskForm();

  addingMaterial: boolean;
  newMaterialForm: NewMaterialForm = new NewMaterialForm();
  materialUseOriginalName: boolean = true;
  materialFakePath: string;
  materialUploadProgress: number;

  addingFileRequirement: boolean;
  newFileRequirementForm: NewFileRequirementForm = new NewFileRequirementForm();

  addingSpecialConsideration: boolean;
  newSpecialConsideration: NewSpecialConsiderationForm = new NewSpecialConsiderationForm();

  editingLatePenalty: boolean;

  constructor(
    private adminService: AdminService,
    private route: ActivatedRoute,
    private titleService: TitleService
  ) {
    this.newFileRequirementForm.is_optional = false;
  }

  ngOnInit() {
    this.taskId = parseInt(this.route.snapshot.paramMap.get('task_id'));

    this.loadingTask = true;
    this.adminService.getTask(this.taskId).pipe(
      finalize(() => this.loadingTask = false)
    ).subscribe(
      task => this.setTask(task),
      error => this.error = error.error
    )
  }

  private setTask(task: Task) {
    const term = task.term;
    this.titleService.setTitle(task.title, `${term.year}S${term.semester}`, term.course.code, 'Management');

    this.task = task;

    this.form.type = task.type;
    this.form.title = task.title;
    this.form.description = task.description;

    this.form.is_team_task = task.is_team_task;
    this.form.team_min_size = task.team_min_size;
    this.form.team_max_size = task.team_max_size;

    this.form.late_penalty = task.late_penalty;
    this.form.submission_attempt_limit = task.submission_attempt_limit;
    this.form.submission_history_limit = task.submission_history_limit;

    this.form.evaluation_method = task.evaluation_method;
    this.form.auto_test_trigger = task.auto_test_trigger;

    if (task.open_time)
      this.form.open_time = moment(task.open_time).format('YYYY-MM-DDTHH:mm');
    else
      this.form.open_time = task.open_time;

    if (task.due_time)
      this.form.due_time = moment(task.due_time).format('YYYY-MM-DDTHH:mm');
    else
      this.form.due_time = task.due_time;

    if (task.close_time)
      this.form.close_time = moment(task.close_time).format('YYYY-MM-DDTHH:mm');
    else
      this.form.close_time = task.close_time;

    // adjust special consideration form
    if (this.task.is_team_task)
      this.newSpecialConsideration.user_name = null;
    else
      this.newSpecialConsideration.team_name = null;
  }

  update(f: NgForm) {
    if (f.invalid)
      return;

    this.updating = true;
    this.adminService.updateTask(this.taskId, this.form).pipe(
      finalize(() => this.updating = false)
    ).subscribe(
      task => {
        this.setTask(task);
        this.success = {msg: 'Updated task successfully'};
      },
      error => this.error = error.error
    )
  }

  addMaterial(f: NgForm, files: FileList) {
    if (f.invalid)
      return;
    if (files.length == 0)
      return;
    const file = files.item(0);

    if (this.materialUseOriginalName)
      this.newMaterialForm.name = file.name;

    this.addingMaterial = true;
    this.adminService.addMaterial(this.taskId, this.newMaterialForm, file).pipe(
      finalize(() => this.addingMaterial = false)
    ).subscribe(
      event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            this.materialUploadProgress = Math.round(100 * event.loaded / event.total);
            break;
          case HttpEventType.Response:
            this.task.materials.push(event.body as Material);
            this.success = {msg: `Uploaded material "${this.newMaterialForm.name}" successfully`}
        }
      },
      error => this.secondaryError = error.error
    )
  }

  updateMaterialSelectFile(material: Material, input: HTMLInputElement) {
    const idx = material.name.lastIndexOf('.');
    input.accept = idx > 0 ? material.name.substring(idx) : "*/*";
    input.click()
  }

  updateMaterial(material: Material, index: number, btn: HTMLElement, input: HTMLInputElement) {
    if (input.files.length == 0)
      return;
    const file = input.files.item(0);
    if (!confirm(`You are going to upload your local file "${file.name}" to update the contents of  material "${material.name}". The old contents will be overwritten but the name will not change. Continue?`)) {
      input.value = '';
      return;
    }

    btn.classList.add('loading', 'disabled');
    this.adminService.updateMaterial(material.id, file).pipe(
      finalize(() => {
        btn.classList.remove('loading', 'disabled');
        input.value = '';
        delete material['_update_progress'];
      })
    ).subscribe(
      event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            material['_update_progress'] = Math.round(100 * event.loaded / event.total);
            break;
          case HttpEventType.Response:
            this.task.materials[index] = (event.body as Material);
            this.success = {msg: `Updated material "${material.name}" successfully`}
        }
      },
      error => this.error = error.error
    )
  }

  deleteMaterial(material: Material, index: number, btn: HTMLElement) {
    if (!confirm(`Really want to delete material "${material.name}"?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteMaterial(material.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.task.materials.splice(index, 1),
      error => this.secondaryError = error.error
    )
  }

  updateFileName(files: FileList) {
    if (this.materialUseOriginalName) {
      if (files.length > 0) {
        this.newMaterialForm.name = files.item(0).name;
      } else {
        this.newMaterialForm.name = null;
      }
    }
  }

  addFileRequirement(f: NgForm) {
    if (f.invalid)
      return;

    this.addingFileRequirement = true;
    this.adminService.addFileRequirement(this.taskId, this.newFileRequirementForm).pipe(
      finalize(() => this.addingFileRequirement = false)
    ).subscribe(
      req => this.task.file_requirements.push(req),
      error => this.secondaryError = error.error
    )
  }

  deleteFileRequirement(req: FileRequirement, index: number, btn: HTMLElement) {
    if (!confirm(`Really want to delete requirement "${req.name}"?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteFileRequirement(req.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.task.file_requirements.splice(index, 1),
      error => this.secondaryError = error.error
    )
  }

  addSpecialConsideration(f: NgForm) {
    if (f.invalid)
      return;

    this.addingSpecialConsideration = true;
    this.adminService.addSpecialConsideration(this.taskId, this.newSpecialConsideration).pipe(
      finalize(() => this.addingSpecialConsideration = false)
    ).subscribe(
      spec => this.task.special_considerations.push(spec),
      error => this.thirdError = error.error
    )
  }

  deleteSpecialConsideration(spec: SpecialConsideration, index: number, btn: HTMLElement) {
    if (!confirm(`Really want to delete special consideration ${spec.id}?`))
      return;

    btn.classList.add('loading', 'disabled');
    this.adminService.deleteSpecialConsiderations(spec.id).pipe(
      finalize(() => btn.classList.remove('loading', 'disabled'))
    ).subscribe(
      () => this.task.special_considerations.splice(index, 1),
      error => this.thirdError = error.error
    )
  }

}
