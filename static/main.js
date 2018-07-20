(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./src/$$_lazy_route_resource lazy recursive":
/*!**********************************************************!*\
  !*** ./src/$$_lazy_route_resource lazy namespace object ***!
  \**********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncaught exception popping up in devtools
	return Promise.resolve().then(function() {
		var e = new Error('Cannot find module "' + req + '".');
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "./src/$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "./src/app/account.service.ts":
/*!************************************!*\
  !*** ./src/app/account.service.ts ***!
  \************************************/
/*! exports provided: AccountService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AccountService", function() { return AccountService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var _log_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./log.service */ "./src/app/log.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var AccountService = /** @class */ (function () {
    function AccountService(http, logService) {
        this.http = http;
        this.api = 'api/account';
        this.logger = logService.get_logger('AccountService');
    }
    AccountService.prototype.get_current_user = function () {
        var _this = this;
        return this.http.get('/api/account/me').pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["tap"])(function (user) { return _this.logger.info("Fetched user info of " + user.name); }));
    };
    AccountService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        }),
        __metadata("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_1__["HttpClient"],
            _log_service__WEBPACK_IMPORTED_MODULE_3__["LogService"]])
    ], AccountService);
    return AccountService;
}());



/***/ }),

/***/ "./src/app/admin-course-edit/admin-course-edit.component.html":
/*!********************************************************************!*\
  !*** ./src/app/admin-course-edit/admin-course-edit.component.html ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-error-message [error]=\"error\"></app-error-message>\n<app-success-message [success]=\"success\"></app-success-message>\n\n<div class=\"ui center aligned active text loader\" *ngIf=\"loadingCourse\">Loading course info...</div>\n\n<div class=\"ui grid stackable two column\" *ngIf=\"course\">\n  <!-- Left Panel -->\n  <div class=\"column\">\n    <div class=\"ui segments\">\n      <!--Header-->\n      <div class=\"ui segment\">\n        <div class=\"ui header\">\n          <i class=\"icon book\"></i>\n          {{course.code}}\n        </div>\n      </div>\n      <!--End of Header-->\n\n      <!-- Basic Info -->\n      <div class=\"ui segment\">\n        <div class=\"ui list horizontal\">\n          <div class=\"item\">\n            <div class=\"header\">ID</div>\n            {{course.id}}\n          </div>\n          <div class=\"item\">\n            <div class=\"header\">Code</div>\n            {{course.code}}\n          </div>\n          <div class=\"item\">\n            <div class=\"header\">Name</div>\n            {{course.name}}\n          </div>\n        </div>\n      </div>\n      <!-- End of Basic Info -->\n\n      <!--Icon Upload-->\n      <div class=\"ui segment\">\n        <div class=\"ui center aligned grid\">\n          <div class=\"column\">\n            <form class=\"ui form\" [ngClass]=\"{'loading': uploadingIcon}\">\n              <div class=\"field\">\n                <label>Icon</label>\n                <input type=\"file\" hidden name=\"icon\" #icon_input [accept]=\"iconValidator.filter.accept.join(',')\" (change)=\"uploadIcon(icon_input)\">\n                <img class=\"ui small centered image\" [src]=\"course.icon\" *ngIf=\"course.icon\">\n                <div class=\"text muted\" *ngIf=\"!course.icon\">(No icon)</div>\n              </div>\n              <button class=\"ui primary button\" type=\"button\" (click)=\"icon_input.click()\">Upload Icon</button>\n              <p>Max size: {{iconValidator.filter.size_limit/1024 | number}}KB, squared image only</p>\n            </form>\n          </div>\n        </div>\n      </div>\n      <!--End of Icon Upload-->\n\n      <!--Lectures-->\n      <div class=\"segment\">\n\n      </div>\n      <!--End of Lectures-->\n    </div>\n  </div>\n  <!-- End of Left Panel -->\n\n  <!--Right Panel-->\n  <div class=\"column\">\n\n  </div>\n  <!--End of Right Panel-->\n</div>\n"

/***/ }),

/***/ "./src/app/admin-course-edit/admin-course-edit.component.less":
/*!********************************************************************!*\
  !*** ./src/app/admin-course-edit/admin-course-edit.component.less ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-course-edit/admin-course-edit.component.ts":
/*!******************************************************************!*\
  !*** ./src/app/admin-course-edit/admin-course-edit.component.ts ***!
  \******************************************************************/
/*! exports provided: AdminCourseEditComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminCourseEditComponent", function() { return AdminCourseEditComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var _upload_util__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../upload-util */ "./src/app/upload-util.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};





var AdminCourseEditComponent = /** @class */ (function () {
    function AdminCourseEditComponent(adminService, route) {
        this.adminService = adminService;
        this.route = route;
        this.iconValidator = new _upload_util__WEBPACK_IMPORTED_MODULE_4__["UploadValidator"](_upload_util__WEBPACK_IMPORTED_MODULE_4__["UploadFilters"].icon);
    }
    AdminCourseEditComponent.prototype.ngOnInit = function () {
        this.course_id = parseInt(this.route.snapshot.paramMap.get('course_id'));
        this.loadCourse();
    };
    AdminCourseEditComponent.prototype.loadCourse = function () {
        var _this = this;
        this.loadingCourse = true;
        this.adminService.getCourse(this.course_id).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["finalize"])(function () { return _this.loadingCourse = false; })).subscribe(function (course) { return _this.course = course; }, function (error) { return _this.error = error.error; });
    };
    AdminCourseEditComponent.prototype.uploadIcon = function (input) {
        var _this = this;
        var files = input.files;
        if (files.length == 0)
            return;
        var file = files.item(0);
        if (!this.iconValidator.check(file)) {
            input.value = ''; // reset
            this.error = this.iconValidator.error;
            return;
        }
        this.uploadingIcon = true;
        this.adminService.updateCourseIcon(this.course_id, file).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["finalize"])(function () {
            _this.uploadingIcon = false;
            input.value = ''; // reset
        })).subscribe(function (course) {
            _this.course = course;
            _this.success = { msg: 'Uploaded course icon successfully' };
        }, function (error) { return _this.error = error.error; });
    };
    AdminCourseEditComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-course-edit',
            template: __webpack_require__(/*! ./admin-course-edit.component.html */ "./src/app/admin-course-edit/admin-course-edit.component.html"),
            styles: [__webpack_require__(/*! ./admin-course-edit.component.less */ "./src/app/admin-course-edit/admin-course-edit.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_2__["AdminService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_1__["ActivatedRoute"]])
    ], AdminCourseEditComponent);
    return AdminCourseEditComponent;
}());



/***/ }),

/***/ "./src/app/admin-course-new/admin-course-new.component.html":
/*!******************************************************************!*\
  !*** ./src/app/admin-course-new/admin-course-new.component.html ***!
  \******************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-error-message [error]=\"error\"></app-error-message>\n<div class=\"ui segment\">\n  <div class=\"ui header dividing\">\n    <i class=\"icon plus\"></i> New Course\n  </div>\n  <form class=\"ui form\" #f=\"ngForm\" (ngSubmit)=\"newTerm(f)\" [ngClass]=\"{'loading': addingCourse}\">\n    <div class=\"field required\" [ngClass]=\"{'error': (code_model.touched || code_model.dirty || f.submitted) && code_model.invalid}\">\n      <label>Code</label>\n      <input type=\"text\" name=\"code\" placeholder='e.g. \"COMP9318\" (at most 16 characters)'\n             required maxlength=\"16\"\n             [(ngModel)]=\"form.code\" #code_model=\"ngModel\">\n      <div class=\"errors\">\n        <label *ngIf=\"code_model.errors?.required\"><i class=\"icon times\"></i> Code is required</label>\n        <label *ngIf=\"code_model.errors?.maxlength\"><i class=\"icon times\"></i> Code is too long</label>\n      </div>\n    </div>\n    <div class=\"field required\" [ngClass]=\"{'error': (name_model.touched || name_model.dirty || f.submitted) && name_model.invalid}\">\n      <label>Name</label>\n      <input type=\"text\" name=\"name\" placeholder='e.g. \"Data Warehousing and Data Mining\" (at most 128 characters)'\n             required maxlength=\"128\"\n             [(ngModel)]=\"form.name\" #name_model=\"ngModel\">\n      <div class=\"errors\">\n        <label *ngIf=\"name_model.errors?.required\"><i class=\"icon times\"></i> Name is required</label>\n        <label *ngIf=\"name_model.errors?.maxlength\"><i class=\"icon times\"></i> Name is too long</label>\n      </div>\n    </div>\n    <button type=\"submit\" class=\"ui primary button fluid\">Add Course</button>\n  </form>\n</div>\n"

/***/ }),

/***/ "./src/app/admin-course-new/admin-course-new.component.less":
/*!******************************************************************!*\
  !*** ./src/app/admin-course-new/admin-course-new.component.less ***!
  \******************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-course-new/admin-course-new.component.ts":
/*!****************************************************************!*\
  !*** ./src/app/admin-course-new/admin-course-new.component.ts ***!
  \****************************************************************/
/*! exports provided: AdminCourseNewComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminCourseNewComponent", function() { return AdminCourseNewComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var AdminCourseNewComponent = /** @class */ (function () {
    function AdminCourseNewComponent(adminService, route, router) {
        this.adminService = adminService;
        this.route = route;
        this.router = router;
        this.form = new _admin_service__WEBPACK_IMPORTED_MODULE_1__["NewCourseForm"]();
    }
    AdminCourseNewComponent.prototype.ngOnInit = function () {
    };
    AdminCourseNewComponent.prototype.newTerm = function (f) {
        var _this = this;
        if (f.invalid)
            return;
        this.addingCourse = true;
        this.adminService.addCourse(this.form).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["finalize"])(function () { return _this.addingCourse = false; })).subscribe(function (course) { return _this.router.navigate(["../courses/" + course.id], { relativeTo: _this.route }); }, function (error) { return _this.error = error.error; });
    };
    AdminCourseNewComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-course-new',
            template: __webpack_require__(/*! ./admin-course-new.component.html */ "./src/app/admin-course-new/admin-course-new.component.html"),
            styles: [__webpack_require__(/*! ./admin-course-new.component.less */ "./src/app/admin-course-new/admin-course-new.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_1__["AdminService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_2__["ActivatedRoute"],
            _angular_router__WEBPACK_IMPORTED_MODULE_2__["Router"]])
    ], AdminCourseNewComponent);
    return AdminCourseNewComponent;
}());



/***/ }),

/***/ "./src/app/admin-courses/admin-courses.component.html":
/*!************************************************************!*\
  !*** ./src/app/admin-courses/admin-courses.component.html ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-error-message [error]=\"error\"></app-error-message>\n<div class=\"top attached ui segment\">\n  <a routerLink=\"../course-new\" class=\"ui primary button\"><i class=\"icon plus\"></i> New Course</a>\n</div>\n<div class=\"ui active text loader center aligned\" *ngIf=\"loadingCourses\">Loading course list...</div>\n<table class=\"ui table bottom attached unstackable celled\" *ngIf=\"courses\">\n  <thead><tr><th>ID</th><th>Code</th><th>Name</th><th class=\"collapsing\">Ops</th></tr></thead>\n  <tbody>\n  <tr *ngFor=\"let course of courses, index as i\">\n    <td>{{course.id}}</td>\n    <td>{{course.code}}</td>\n    <td>{{course.name}}</td>\n    <td class=\"collapsing\">\n      <div class=\"ui buttons small\">\n        <a routerLink=\"../courses/{{course.id}}\" class=\"ui button icon\"><i class=\"edit icon\"></i></a>\n        <a (click)=\"deleteCourse(course, i, btn_delete_course)\" #btn_delete_course class=\"ui red button icon\"><i class=\"trash icon\"></i></a>\n      </div>\n    </td>\n  </tr>\n  </tbody>\n</table>\n"

/***/ }),

/***/ "./src/app/admin-courses/admin-courses.component.less":
/*!************************************************************!*\
  !*** ./src/app/admin-courses/admin-courses.component.less ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-courses/admin-courses.component.ts":
/*!**********************************************************!*\
  !*** ./src/app/admin-courses/admin-courses.component.ts ***!
  \**********************************************************/
/*! exports provided: AdminCoursesComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminCoursesComponent", function() { return AdminCoursesComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var AdminCoursesComponent = /** @class */ (function () {
    function AdminCoursesComponent(adminService) {
        this.adminService = adminService;
    }
    AdminCoursesComponent.prototype.ngOnInit = function () {
        this.loadTerms();
    };
    AdminCoursesComponent.prototype.loadTerms = function () {
        var _this = this;
        this.loadingCourses = true;
        this.adminService.getCourses().pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["finalize"])(function () { return _this.loadingCourses = false; })).subscribe(function (courses) { return _this.courses = courses; }, function (error) { return _this.error = error.error; });
    };
    AdminCoursesComponent.prototype.deleteCourse = function (course, index, btn) {
        var _this = this;
        if (!confirm("Really want to delete course \"" + course.code + " - " + course.name + "\"? This is not recoverable!"))
            return;
        btn.classList.add('loading', 'disabled');
        this.adminService.deleteCourse(course.id).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["finalize"])(function () { return btn.classList.remove('loading', 'disabled'); })).subscribe(function () { return _this.courses.splice(index, 1); }, function (error) { return _this.error = error.error; });
    };
    AdminCoursesComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-courses',
            template: __webpack_require__(/*! ./admin-courses.component.html */ "./src/app/admin-courses/admin-courses.component.html"),
            styles: [__webpack_require__(/*! ./admin-courses.component.less */ "./src/app/admin-courses/admin-courses.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_1__["AdminService"]])
    ], AdminCoursesComponent);
    return AdminCoursesComponent;
}());



/***/ }),

/***/ "./src/app/admin-term-edit/admin-term-edit.component.html":
/*!****************************************************************!*\
  !*** ./src/app/admin-term-edit/admin-term-edit.component.html ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui segments\">\n  <div class=\"ui segment\">\n    <form class=\"ui form\" #f=\"ngForm\" (ngSubmit)=\"updateTerm(f)\" [ngClass]=\"{'loading': updatingTerm}\">\n      <div class=\"field required\" [ngClass]=\"{'error': (title_model.touched || title_model.dirty || f.submitted) && title_model.invalid}\">\n        <label>Title</label>\n        <input type=\"text\" name=\"title\" placeholder='e.g. \"COMP9318 18s1\" (at most 128 characters)'\n               required maxlength=\"128\"\n               [(ngModel)]=\"form.title\" #title_model=\"ngModel\">\n        <div class=\"errors\">\n          <label *ngIf=\"title_model.errors?.required\">Title is required</label>\n          <label *ngIf=\"title_model.errors?.maxlength\">Title is too long</label>\n        </div>\n      </div>\n      <div class=\"field\" [ngClass]=\"{'error': (desc_model.touched || desc_model.dirty || f.submitted) && desc_model.invalid}\">\n        <label>Description</label>\n        <input type=\"text\" name=\"description\" placeholder='A general introduction of this course or term (at most 256 characters)'\n               maxlength=\"256\"\n               [(ngModel)]=\"form.description\" #desc_model=\"ngModel\">\n        <div class=\"errors\">\n          <label *ngIf=\"desc_model.errors?.maxlength\">Description is too long</label>\n        </div>\n      </div>\n      <button type=\"submit\" class=\"ui primary button fluid\">Add</button>\n    </form>\n  </div>\n</div>\n"

/***/ }),

/***/ "./src/app/admin-term-edit/admin-term-edit.component.less":
/*!****************************************************************!*\
  !*** ./src/app/admin-term-edit/admin-term-edit.component.less ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-term-edit/admin-term-edit.component.ts":
/*!**************************************************************!*\
  !*** ./src/app/admin-term-edit/admin-term-edit.component.ts ***!
  \**************************************************************/
/*! exports provided: AdminTermEditComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminTermEditComponent", function() { return AdminTermEditComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var AdminTermEditComponent = /** @class */ (function () {
    function AdminTermEditComponent(adminService, route) {
        this.adminService = adminService;
        this.route = route;
    }
    AdminTermEditComponent.prototype.ngOnInit = function () {
        this.termId = parseInt(this.route.snapshot.paramMap.get('team_id'));
        this.loadTerm();
    };
    AdminTermEditComponent.prototype.loadTerm = function () {
        var _this = this;
        this.loadingTerm = true;
        this.adminService.getTerm(this.termId).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["finalize"])(function () { return _this.loadingTerm = false; })).subscribe(function (term) { return _this.term = term; }, function (error) { return _this.error = error.error; });
    };
    AdminTermEditComponent.prototype.updateTerm = function (f) {
        if (f.invalid)
            return;
        this.adminService.updateTerm();
    };
    AdminTermEditComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-term-edit',
            template: __webpack_require__(/*! ./admin-term-edit.component.html */ "./src/app/admin-term-edit/admin-term-edit.component.html"),
            styles: [__webpack_require__(/*! ./admin-term-edit.component.less */ "./src/app/admin-term-edit/admin-term-edit.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_1__["AdminService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_2__["ActivatedRoute"]])
    ], AdminTermEditComponent);
    return AdminTermEditComponent;
}());



/***/ }),

/***/ "./src/app/admin-term-new/admin-term-new.component.html":
/*!**************************************************************!*\
  !*** ./src/app/admin-term-new/admin-term-new.component.html ***!
  \**************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-error-message [error]=\"error\"></app-error-message>\n<div class=\"ui segment\">\n  <div class=\"ui header dividing\">\n    <i class=\"icon plus\"></i> New Term\n  </div>\n  <form class=\"ui form\" #f=\"ngForm\" (ngSubmit)=\"newTerm(f)\" [ngClass]=\"{'loading': addingTerm}\">\n    <div class=\"field required\" [ngClass]=\"{'error': (title_model.touched || title_model.dirty || f.submitted) && title_model.invalid}\">\n      <label>Title</label>\n      <input type=\"text\" name=\"title\" placeholder='e.g. \"COMP9318 18s1\" (at most 128 characters)'\n             required maxlength=\"128\"\n             [(ngModel)]=\"form.title\" #title_model=\"ngModel\">\n      <div class=\"errors\">\n        <label *ngIf=\"title_model.errors?.required\">Title is required</label>\n        <label *ngIf=\"title_model.errors?.maxlength\">Title is too long</label>\n      </div>\n    </div>\n    <div class=\"field\" [ngClass]=\"{'error': (desc_model.touched || desc_model.dirty || f.submitted) && desc_model.invalid}\">\n      <label>Description</label>\n      <input type=\"text\" name=\"description\" placeholder='A general introduction of this course or term (at most 256 characters)'\n             maxlength=\"256\"\n             [(ngModel)]=\"form.description\" #desc_model=\"ngModel\">\n      <div class=\"errors\">\n        <label *ngIf=\"desc_model.errors?.maxlength\">Description is too long</label>\n      </div>\n    </div>\n    <button type=\"submit\" class=\"ui primary button fluid\">Add</button>\n  </form>\n</div>\n"

/***/ }),

/***/ "./src/app/admin-term-new/admin-term-new.component.less":
/*!**************************************************************!*\
  !*** ./src/app/admin-term-new/admin-term-new.component.less ***!
  \**************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-term-new/admin-term-new.component.ts":
/*!************************************************************!*\
  !*** ./src/app/admin-term-new/admin-term-new.component.ts ***!
  \************************************************************/
/*! exports provided: AdminTermNewComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminTermNewComponent", function() { return AdminTermNewComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var AdminTermNewComponent = /** @class */ (function () {
    function AdminTermNewComponent(adminService, route, router) {
        this.adminService = adminService;
        this.route = route;
        this.router = router;
        this.form = new _admin_service__WEBPACK_IMPORTED_MODULE_1__["NewTermForm"]();
    }
    AdminTermNewComponent.prototype.ngOnInit = function () {
    };
    AdminTermNewComponent.prototype.newTerm = function (f) {
        var _this = this;
        if (f.invalid)
            return;
        this.addingTerm = true;
        this.adminService.addTerm(this.form).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["finalize"])(function () { return _this.addingTerm = false; })).subscribe(function (term) { return _this.router.navigate(["../terms/" + term.id], { relativeTo: _this.route }); }, function (error) { return _this.error = error.error; });
    };
    AdminTermNewComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-term-new',
            template: __webpack_require__(/*! ./admin-term-new.component.html */ "./src/app/admin-term-new/admin-term-new.component.html"),
            styles: [__webpack_require__(/*! ./admin-term-new.component.less */ "./src/app/admin-term-new/admin-term-new.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_1__["AdminService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_3__["ActivatedRoute"],
            _angular_router__WEBPACK_IMPORTED_MODULE_3__["Router"]])
    ], AdminTermNewComponent);
    return AdminTermNewComponent;
}());



/***/ }),

/***/ "./src/app/admin-terms/admin-terms.component.html":
/*!********************************************************!*\
  !*** ./src/app/admin-terms/admin-terms.component.html ***!
  \********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-error-message [error]=\"error\"></app-error-message>\n<div class=\"top attached ui segment\">\n  <a routerLink=\"../term-new\" class=\"ui primary button\"><i class=\"icon plus\"></i> New Term</a>\n</div>\n<div class=\"ui active text loader center aligned\" *ngIf=\"loadingTerms\">Loading term list...</div>\n<table class=\"ui table bottom attached unstackable celled\" *ngIf=\"terms\">\n  <thead><tr><th>ID</th><th>Title</th><th>Description</th><th class=\"collapsing\">Ops</th></tr></thead>\n  <tbody>\n  <tr *ngFor=\"let term of terms, index as i\">\n    <td>{{term.id}}</td>\n    <td>{{term.title}}</td>\n    <td>{{term.description}}</td>\n    <td class=\"collapsing\">\n      <div class=\"ui buttons small\">\n        <a routerLink=\"../terms/{{term.id}}\" class=\"ui button icon\"><i class=\"edit icon\"></i></a>\n        <a (click)=\"deleteTerm(term, i, btn_delete_term)\" #btn_delete_term class=\"ui red button icon\"><i class=\"trash icon\"></i></a>\n      </div>\n    </td>\n  </tr>\n  </tbody>\n</table>\n"

/***/ }),

/***/ "./src/app/admin-terms/admin-terms.component.less":
/*!********************************************************!*\
  !*** ./src/app/admin-terms/admin-terms.component.less ***!
  \********************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin-terms/admin-terms.component.ts":
/*!******************************************************!*\
  !*** ./src/app/admin-terms/admin-terms.component.ts ***!
  \******************************************************/
/*! exports provided: AdminTermsComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminTermsComponent", function() { return AdminTermsComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _admin_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../admin.service */ "./src/app/admin.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var AdminTermsComponent = /** @class */ (function () {
    function AdminTermsComponent(adminService) {
        this.adminService = adminService;
    }
    AdminTermsComponent.prototype.ngOnInit = function () {
        this.loadTerms();
    };
    AdminTermsComponent.prototype.loadTerms = function () {
        var _this = this;
        this.loadingTerms = true;
        this.adminService.getTerms().pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["finalize"])(function () { return _this.loadingTerms = false; })).subscribe(function (terms) { return _this.terms = terms; }, function (error) { return _this.error = error.error; });
    };
    AdminTermsComponent.prototype.deleteTerm = function (term, index, btn) {
        var _this = this;
        if (!confirm("Really want to delete term " + term.title + "? This is not recoverable!"))
            return;
        btn.classList.add('loading', 'disabled');
        this.adminService.deleteTerm(term.id).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_2__["finalize"])(function () { return btn.classList.remove('loading', 'disabled'); })).subscribe(function () { return _this.terms.splice(index, 1); }, function (error) { return _this.error = error.error; });
    };
    AdminTermsComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin-terms',
            template: __webpack_require__(/*! ./admin-terms.component.html */ "./src/app/admin-terms/admin-terms.component.html"),
            styles: [__webpack_require__(/*! ./admin-terms.component.less */ "./src/app/admin-terms/admin-terms.component.less")]
        }),
        __metadata("design:paramtypes", [_admin_service__WEBPACK_IMPORTED_MODULE_1__["AdminService"]])
    ], AdminTermsComponent);
    return AdminTermsComponent;
}());



/***/ }),

/***/ "./src/app/admin.guard.ts":
/*!********************************!*\
  !*** ./src/app/admin.guard.ts ***!
  \********************************/
/*! exports provided: AdminGuard */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminGuard", function() { return AdminGuard; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _account_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./account.service */ "./src/app/account.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
/* harmony import */ var rxjs_internal_observable_of__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! rxjs/internal/observable/of */ "./node_modules/rxjs/internal/observable/of.js");
/* harmony import */ var rxjs_internal_observable_of__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(rxjs_internal_observable_of__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _log_service__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./log.service */ "./src/app/log.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};






var AdminGuard = /** @class */ (function () {
    function AdminGuard(accountService, router, logService) {
        this.accountService = accountService;
        this.router = router;
        this.logService = logService;
        this.logger = logService.get_logger('AdminGuard');
    }
    AdminGuard.prototype.canActivate = function (next, state) {
        var _this = this;
        return this.accountService.get_current_user().pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["map"])(function (user) {
            if (user != null) {
                for (var _i = 0, _a = user.groups; _i < _a.length; _i++) {
                    var group = _a[_i];
                    if (group.name == 'admin') {
                        _this.logger.info('Admin verified');
                        return true;
                    }
                }
            }
            _this.router.navigate(['/forbidden']);
            _this.logger.warn('Not admin');
            return false;
        }), Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["catchError"])(function (error) {
            var redirect_url = error.error.redirect_url;
            if (redirect_url) {
                _this.logger.warn('OAuth session closed. Redirect required');
                window.location.href = redirect_url;
            }
            else {
                _this.logger.error("Failed to get user info: " + error.error.msg);
                _this.router.navigate(['/forbidden']);
            }
            return Object(rxjs_internal_observable_of__WEBPACK_IMPORTED_MODULE_4__["of"])(false);
        }));
    };
    AdminGuard = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        }),
        __metadata("design:paramtypes", [_account_service__WEBPACK_IMPORTED_MODULE_2__["AccountService"],
            _angular_router__WEBPACK_IMPORTED_MODULE_1__["Router"],
            _log_service__WEBPACK_IMPORTED_MODULE_5__["LogService"]])
    ], AdminGuard);
    return AdminGuard;
}());



/***/ }),

/***/ "./src/app/admin.service.ts":
/*!**********************************!*\
  !*** ./src/app/admin.service.ts ***!
  \**********************************/
/*! exports provided: NewCourseForm, AdminService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "NewCourseForm", function() { return NewCourseForm; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminService", function() { return AdminService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var _log_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./log.service */ "./src/app/log.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};




var NewCourseForm = /** @class */ (function () {
    function NewCourseForm() {
    }
    return NewCourseForm;
}());

var AdminService = /** @class */ (function () {
    function AdminService(http, logService) {
        this.http = http;
        this.logService = logService;
        this.api = 'api/admin';
        this.logger = this.logService.get_logger('AdminService');
    }
    AdminService.prototype.getCourses = function () {
        var _this = this;
        return this.http.get(this.api + "/courses").pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["tap"])(function (courses) { return _this.logger.info("Fetched course list (" + courses.length + " courses)"); }));
    };
    AdminService.prototype.addCourse = function (form) {
        var _this = this;
        return this.http.post(this.api + "/courses", form).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["tap"])(function (term) { return _this.logger.info("Added new course \"" + term.code + "\""); }));
    };
    AdminService.prototype.deleteCourse = function (tid) {
        var _this = this;
        return this.http.delete(this.api + "/courses/" + tid).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["tap"])(function () { return _this.logger.info("Deleted course (id: " + tid + ")"); }));
    };
    AdminService.prototype.getCourse = function (tid) {
        var _this = this;
        return this.http.get(this.api + "/courses/" + tid).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["tap"])(function (term) { return _this.logger.info("Fetched info of course \"" + term.code + "\""); }));
    };
    AdminService.prototype.updateCourseIcon = function (tid, iconFile) {
        var _this = this;
        var form = new FormData();
        form.append('icon', iconFile);
        return this.http.put(this.api + "/courses/" + tid, form).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_3__["tap"])(function (term) { return _this.logger.info("Updated icon of course " + term.code); }));
    };
    AdminService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        }),
        __metadata("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_1__["HttpClient"],
            _log_service__WEBPACK_IMPORTED_MODULE_2__["LogService"]])
    ], AdminService);
    return AdminService;
}());



/***/ }),

/***/ "./src/app/admin/admin.component.html":
/*!********************************************!*\
  !*** ./src/app/admin/admin.component.html ***!
  \********************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui container\">\n  <h1 class=\"ui header\">\n    UNSW Submit\n  </h1>\n  <div class=\"ui segment\">\n    <button class=\"ui button\" routerLink=\"courses\">Courses</button>\n  </div>\n  <router-outlet></router-outlet>\n</div>\n"

/***/ }),

/***/ "./src/app/admin/admin.component.less":
/*!********************************************!*\
  !*** ./src/app/admin/admin.component.less ***!
  \********************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/admin/admin.component.ts":
/*!******************************************!*\
  !*** ./src/app/admin/admin.component.ts ***!
  \******************************************/
/*! exports provided: AdminComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AdminComponent", function() { return AdminComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var AdminComponent = /** @class */ (function () {
    function AdminComponent() {
    }
    AdminComponent.prototype.ngOnInit = function () {
    };
    AdminComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-admin',
            template: __webpack_require__(/*! ./admin.component.html */ "./src/app/admin/admin.component.html"),
            styles: [__webpack_require__(/*! ./admin.component.less */ "./src/app/admin/admin.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], AdminComponent);
    return AdminComponent;
}());



/***/ }),

/***/ "./src/app/app-routing.module.ts":
/*!***************************************!*\
  !*** ./src/app/app-routing.module.ts ***!
  \***************************************/
/*! exports provided: AppRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppRoutingModule", function() { return AppRoutingModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _home_home_component__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./home/home.component */ "./src/app/home/home.component.ts");
/* harmony import */ var _admin_admin_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./admin/admin.component */ "./src/app/admin/admin.component.ts");
/* harmony import */ var _admin_guard__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./admin.guard */ "./src/app/admin.guard.ts");
/* harmony import */ var _admin_terms_admin_terms_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./admin-terms/admin-terms.component */ "./src/app/admin-terms/admin-terms.component.ts");
/* harmony import */ var _admin_term_new_admin_term_new_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./admin-term-new/admin-term-new.component */ "./src/app/admin-term-new/admin-term-new.component.ts");
/* harmony import */ var _admin_term_edit_admin_term_edit_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./admin-term-edit/admin-term-edit.component */ "./src/app/admin-term-edit/admin-term-edit.component.ts");
/* harmony import */ var _forbidden_forbidden_component__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./forbidden/forbidden.component */ "./src/app/forbidden/forbidden.component.ts");
/* harmony import */ var _not_found_not_found_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./not-found/not-found.component */ "./src/app/not-found/not-found.component.ts");
/* harmony import */ var _admin_courses_admin_courses_component__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./admin-courses/admin-courses.component */ "./src/app/admin-courses/admin-courses.component.ts");
/* harmony import */ var _admin_course_new_admin_course_new_component__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./admin-course-new/admin-course-new.component */ "./src/app/admin-course-new/admin-course-new.component.ts");
/* harmony import */ var _admin_course_edit_admin_course_edit_component__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(/*! ./admin-course-edit/admin-course-edit.component */ "./src/app/admin-course-edit/admin-course-edit.component.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};













var routes = [
    { path: '', pathMatch: 'full', component: _home_home_component__WEBPACK_IMPORTED_MODULE_2__["HomeComponent"] },
    {
        path: 'admin',
        component: _admin_admin_component__WEBPACK_IMPORTED_MODULE_3__["AdminComponent"],
        canActivate: [_admin_guard__WEBPACK_IMPORTED_MODULE_4__["AdminGuard"]],
        children: [
            { path: '', pathMatch: 'full', redirectTo: 'courses' },
            { path: 'courses', component: _admin_courses_admin_courses_component__WEBPACK_IMPORTED_MODULE_10__["AdminCoursesComponent"] },
            { path: 'course-new', component: _admin_course_new_admin_course_new_component__WEBPACK_IMPORTED_MODULE_11__["AdminCourseNewComponent"] },
            { path: 'courses/:course_id', component: _admin_course_edit_admin_course_edit_component__WEBPACK_IMPORTED_MODULE_12__["AdminCourseEditComponent"] },
            { path: 'courses/:course_id/terms', component: _admin_terms_admin_terms_component__WEBPACK_IMPORTED_MODULE_5__["AdminTermsComponent"] },
            { path: 'courses/:course_id/term-new', component: _admin_term_new_admin_term_new_component__WEBPACK_IMPORTED_MODULE_6__["AdminTermNewComponent"] },
            { path: 'terms/:team_id', component: _admin_term_edit_admin_term_edit_component__WEBPACK_IMPORTED_MODULE_7__["AdminTermEditComponent"] }
        ]
    },
    { path: 'forbidden', component: _forbidden_forbidden_component__WEBPACK_IMPORTED_MODULE_8__["ForbiddenComponent"] },
    { path: '**', component: _not_found_not_found_component__WEBPACK_IMPORTED_MODULE_9__["NotFoundComponent"] }
];
var AppRoutingModule = /** @class */ (function () {
    function AppRoutingModule() {
    }
    AppRoutingModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [_angular_router__WEBPACK_IMPORTED_MODULE_1__["RouterModule"].forRoot(routes)],
            exports: [_angular_router__WEBPACK_IMPORTED_MODULE_1__["RouterModule"]]
        })
    ], AppRoutingModule);
    return AppRoutingModule;
}());



/***/ }),

/***/ "./src/app/app.component.html":
/*!************************************!*\
  !*** ./src/app/app.component.html ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<router-outlet></router-outlet>\n"

/***/ }),

/***/ "./src/app/app.component.less":
/*!************************************!*\
  !*** ./src/app/app.component.less ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/app.component.ts":
/*!**********************************!*\
  !*** ./src/app/app.component.ts ***!
  \**********************************/
/*! exports provided: AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};

var AppComponent = /** @class */ (function () {
    function AppComponent() {
        this.title = 'app';
    }
    AppComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-root',
            template: __webpack_require__(/*! ./app.component.html */ "./src/app/app.component.html"),
            styles: [__webpack_require__(/*! ./app.component.less */ "./src/app/app.component.less")]
        })
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm5/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _app_routing_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app-routing.module */ "./src/app/app-routing.module.ts");
/* harmony import */ var _app_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./app.component */ "./src/app/app.component.ts");
/* harmony import */ var _admin_admin_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./admin/admin.component */ "./src/app/admin/admin.component.ts");
/* harmony import */ var _admin_terms_admin_terms_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./admin-terms/admin-terms.component */ "./src/app/admin-terms/admin-terms.component.ts");
/* harmony import */ var _admin_term_edit_admin_term_edit_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./admin-term-edit/admin-term-edit.component */ "./src/app/admin-term-edit/admin-term-edit.component.ts");
/* harmony import */ var _admin_term_new_admin_term_new_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./admin-term-new/admin-term-new.component */ "./src/app/admin-term-new/admin-term-new.component.ts");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _home_home_component__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./home/home.component */ "./src/app/home/home.component.ts");
/* harmony import */ var _forbidden_forbidden_component__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./forbidden/forbidden.component */ "./src/app/forbidden/forbidden.component.ts");
/* harmony import */ var _not_found_not_found_component__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(/*! ./not-found/not-found.component */ "./src/app/not-found/not-found.component.ts");
/* harmony import */ var _error_message_error_message_component__WEBPACK_IMPORTED_MODULE_13__ = __webpack_require__(/*! ./error-message/error-message.component */ "./src/app/error-message/error-message.component.ts");
/* harmony import */ var _admin_courses_admin_courses_component__WEBPACK_IMPORTED_MODULE_14__ = __webpack_require__(/*! ./admin-courses/admin-courses.component */ "./src/app/admin-courses/admin-courses.component.ts");
/* harmony import */ var _admin_course_edit_admin_course_edit_component__WEBPACK_IMPORTED_MODULE_15__ = __webpack_require__(/*! ./admin-course-edit/admin-course-edit.component */ "./src/app/admin-course-edit/admin-course-edit.component.ts");
/* harmony import */ var _admin_course_new_admin_course_new_component__WEBPACK_IMPORTED_MODULE_16__ = __webpack_require__(/*! ./admin-course-new/admin-course-new.component */ "./src/app/admin-course-new/admin-course-new.component.ts");
/* harmony import */ var _success_message_success_message_component__WEBPACK_IMPORTED_MODULE_17__ = __webpack_require__(/*! ./success-message/success-message.component */ "./src/app/success-message/success-message.component.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};


















var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
            declarations: [
                _app_component__WEBPACK_IMPORTED_MODULE_3__["AppComponent"],
                _admin_admin_component__WEBPACK_IMPORTED_MODULE_4__["AdminComponent"],
                _admin_terms_admin_terms_component__WEBPACK_IMPORTED_MODULE_5__["AdminTermsComponent"],
                _admin_term_edit_admin_term_edit_component__WEBPACK_IMPORTED_MODULE_6__["AdminTermEditComponent"],
                _admin_term_new_admin_term_new_component__WEBPACK_IMPORTED_MODULE_7__["AdminTermNewComponent"],
                _home_home_component__WEBPACK_IMPORTED_MODULE_10__["HomeComponent"],
                _forbidden_forbidden_component__WEBPACK_IMPORTED_MODULE_11__["ForbiddenComponent"],
                _not_found_not_found_component__WEBPACK_IMPORTED_MODULE_12__["NotFoundComponent"],
                _error_message_error_message_component__WEBPACK_IMPORTED_MODULE_13__["ErrorMessageComponent"],
                _admin_courses_admin_courses_component__WEBPACK_IMPORTED_MODULE_14__["AdminCoursesComponent"],
                _admin_course_edit_admin_course_edit_component__WEBPACK_IMPORTED_MODULE_15__["AdminCourseEditComponent"],
                _admin_course_new_admin_course_new_component__WEBPACK_IMPORTED_MODULE_16__["AdminCourseNewComponent"],
                _success_message_success_message_component__WEBPACK_IMPORTED_MODULE_17__["SuccessMessageComponent"]
            ],
            imports: [
                _angular_platform_browser__WEBPACK_IMPORTED_MODULE_0__["BrowserModule"],
                _app_routing_module__WEBPACK_IMPORTED_MODULE_2__["AppRoutingModule"],
                _angular_common_http__WEBPACK_IMPORTED_MODULE_8__["HttpClientModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_9__["FormsModule"]
            ],
            providers: [],
            bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_3__["AppComponent"]]
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "./src/app/error-message/error-message.component.html":
/*!************************************************************!*\
  !*** ./src/app/error-message/error-message.component.html ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui error message\" *ngIf=\"error\">\n  <i class=\"close icon\" (click)=\"error=undefined\"></i>\n  <div class=\"header\"><i class=\"times circle icon\"></i> {{error.msg||'Unexpected Error'}}</div>\n  <p *ngIf=\"error.msg\">{{error.detail}}</p>\n  <p *ngIf=\"!error.msg\">{{error}}</p>\n</div>\n"

/***/ }),

/***/ "./src/app/error-message/error-message.component.less":
/*!************************************************************!*\
  !*** ./src/app/error-message/error-message.component.less ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ":host {\n  display: block;\n  margin-top: 1em;\n  margin-bottom: 1em;\n}\n:host:first-child {\n  margin-top: 0;\n}\n:host:last-child {\n  margin-bottom: 0;\n}\n"

/***/ }),

/***/ "./src/app/error-message/error-message.component.ts":
/*!**********************************************************!*\
  !*** ./src/app/error-message/error-message.component.ts ***!
  \**********************************************************/
/*! exports provided: ErrorMessageComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ErrorMessageComponent", function() { return ErrorMessageComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _models__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../models */ "./src/app/models.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var ErrorMessageComponent = /** @class */ (function () {
    function ErrorMessageComponent() {
    }
    ErrorMessageComponent.prototype.ngOnInit = function () {
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", _models__WEBPACK_IMPORTED_MODULE_1__["ErrorMessage"])
    ], ErrorMessageComponent.prototype, "error", void 0);
    ErrorMessageComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-error-message',
            template: __webpack_require__(/*! ./error-message.component.html */ "./src/app/error-message/error-message.component.html"),
            styles: [__webpack_require__(/*! ./error-message.component.less */ "./src/app/error-message/error-message.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], ErrorMessageComponent);
    return ErrorMessageComponent;
}());



/***/ }),

/***/ "./src/app/forbidden/forbidden.component.html":
/*!****************************************************!*\
  !*** ./src/app/forbidden/forbidden.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui middle aligned center aligned padded stackable grid\">\n  <div class=\"column\">\n    <div class=\"ui icon header\">\n      <i class=\"ui dont icon\"></i>\n      Permission Denied\n    </div>\n  </div>\n</div>\n"

/***/ }),

/***/ "./src/app/forbidden/forbidden.component.less":
/*!****************************************************!*\
  !*** ./src/app/forbidden/forbidden.component.less ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".grid {\n  height: 100%;\n}\n"

/***/ }),

/***/ "./src/app/forbidden/forbidden.component.ts":
/*!**************************************************!*\
  !*** ./src/app/forbidden/forbidden.component.ts ***!
  \**************************************************/
/*! exports provided: ForbiddenComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ForbiddenComponent", function() { return ForbiddenComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var ForbiddenComponent = /** @class */ (function () {
    function ForbiddenComponent() {
    }
    ForbiddenComponent.prototype.ngOnInit = function () {
    };
    ForbiddenComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-forbidden',
            template: __webpack_require__(/*! ./forbidden.component.html */ "./src/app/forbidden/forbidden.component.html"),
            styles: [__webpack_require__(/*! ./forbidden.component.less */ "./src/app/forbidden/forbidden.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], ForbiddenComponent);
    return ForbiddenComponent;
}());



/***/ }),

/***/ "./src/app/home/home.component.html":
/*!******************************************!*\
  !*** ./src/app/home/home.component.html ***!
  \******************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<button class=\"ui violet button\" routerLink=\"admin\">Management</button>\n<a href=\"http://localhost:8077/account/logout\" class=\"ui teal button\">Logout</a>\n"

/***/ }),

/***/ "./src/app/home/home.component.less":
/*!******************************************!*\
  !*** ./src/app/home/home.component.less ***!
  \******************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ""

/***/ }),

/***/ "./src/app/home/home.component.ts":
/*!****************************************!*\
  !*** ./src/app/home/home.component.ts ***!
  \****************************************/
/*! exports provided: HomeComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HomeComponent", function() { return HomeComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var HomeComponent = /** @class */ (function () {
    function HomeComponent() {
    }
    HomeComponent.prototype.ngOnInit = function () {
    };
    HomeComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-home',
            template: __webpack_require__(/*! ./home.component.html */ "./src/app/home/home.component.html"),
            styles: [__webpack_require__(/*! ./home.component.less */ "./src/app/home/home.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], HomeComponent);
    return HomeComponent;
}());



/***/ }),

/***/ "./src/app/log.service.ts":
/*!********************************!*\
  !*** ./src/app/log.service.ts ***!
  \********************************/
/*! exports provided: Logger, LogService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Logger", function() { return Logger; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LogService", function() { return LogService; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var Logger = /** @class */ (function () {
    function Logger() {
    }
    return Logger;
}());

var LogService = /** @class */ (function () {
    function LogService() {
        this.css_tag = 'background: white; padding: 0 3px 0 3px; font-weight: bold; color: black; border-left: 4px solid;';
        this.css_message = '';
    }
    LogService.prototype.get_logger = function (tag) {
        var logger = new Logger();
        logger.debug = console.debug.bind(window.console, "%c" + tag + "%c %s", this.css_tag + 'border-color: #767676;', this.css_message);
        logger.info = console.info.bind(window.console, "%c" + tag + "%c %s", this.css_tag + 'border-color: #2185d0;', this.css_message);
        logger.warn = console.warn.bind(window.console, "%c" + tag + "%c %s", this.css_tag + 'border-color: #fbbd08;', this.css_message);
        logger.error = console.error.bind(window.console, "%c" + tag + "%c %s", this.css_tag + 'border-color: #db2828;', this.css_message);
        return logger;
    };
    LogService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root'
        }),
        __metadata("design:paramtypes", [])
    ], LogService);
    return LogService;
}());



/***/ }),

/***/ "./src/app/models.ts":
/*!***************************!*\
  !*** ./src/app/models.ts ***!
  \***************************/
/*! exports provided: SuccessMessage, ErrorMessage, User, Group, Course, Term */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SuccessMessage", function() { return SuccessMessage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ErrorMessage", function() { return ErrorMessage; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "User", function() { return User; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Group", function() { return Group; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Course", function() { return Course; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Term", function() { return Term; });
var SuccessMessage = /** @class */ (function () {
    function SuccessMessage() {
    }
    return SuccessMessage;
}());

var ErrorMessage = /** @class */ (function () {
    function ErrorMessage() {
    }
    return ErrorMessage;
}());

var User = /** @class */ (function () {
    function User() {
    }
    return User;
}());

var Group = /** @class */ (function () {
    function Group() {
    }
    return Group;
}());

var Course = /** @class */ (function () {
    function Course() {
    }
    return Course;
}());

var Term = /** @class */ (function () {
    function Term() {
    }
    return Term;
}());



/***/ }),

/***/ "./src/app/not-found/not-found.component.html":
/*!****************************************************!*\
  !*** ./src/app/not-found/not-found.component.html ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui middle aligned center aligned padded stackable grid\">\n  <div class=\"column\">\n    <div class=\"ui icon header\">\n      <i class=\"ui dont icon\"></i>\n      Page Not Found\n    </div>\n  </div>\n</div>\n"

/***/ }),

/***/ "./src/app/not-found/not-found.component.less":
/*!****************************************************!*\
  !*** ./src/app/not-found/not-found.component.less ***!
  \****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".grid {\n  height: 100%;\n}\n"

/***/ }),

/***/ "./src/app/not-found/not-found.component.ts":
/*!**************************************************!*\
  !*** ./src/app/not-found/not-found.component.ts ***!
  \**************************************************/
/*! exports provided: NotFoundComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "NotFoundComponent", function() { return NotFoundComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var NotFoundComponent = /** @class */ (function () {
    function NotFoundComponent() {
    }
    NotFoundComponent.prototype.ngOnInit = function () {
    };
    NotFoundComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-not-found',
            template: __webpack_require__(/*! ./not-found.component.html */ "./src/app/not-found/not-found.component.html"),
            styles: [__webpack_require__(/*! ./not-found.component.less */ "./src/app/not-found/not-found.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], NotFoundComponent);
    return NotFoundComponent;
}());



/***/ }),

/***/ "./src/app/success-message/success-message.component.html":
/*!****************************************************************!*\
  !*** ./src/app/success-message/success-message.component.html ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"ui success message\" *ngIf=\"success\">\n  <i class=\"close icon\" (click)=\"success=undefined\"></i>\n  <div class=\"header\"><i class=\"check circle icon\"></i> {{success.msg||'Success'}}</div>\n  <p *ngIf=\"success.msg\">{{success.detail}}</p>\n  <p *ngIf=\"!success.msg\">{{success}}</p>\n</div>\n"

/***/ }),

/***/ "./src/app/success-message/success-message.component.less":
/*!****************************************************************!*\
  !*** ./src/app/success-message/success-message.component.less ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ":host {\n  display: block;\n  margin-top: 1em;\n  margin-bottom: 1em;\n}\n:host:first-child {\n  margin-top: 0;\n}\n:host:last-child {\n  margin-bottom: 0;\n}\n"

/***/ }),

/***/ "./src/app/success-message/success-message.component.ts":
/*!**************************************************************!*\
  !*** ./src/app/success-message/success-message.component.ts ***!
  \**************************************************************/
/*! exports provided: SuccessMessageComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SuccessMessageComponent", function() { return SuccessMessageComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _models__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../models */ "./src/app/models.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var SuccessMessageComponent = /** @class */ (function () {
    function SuccessMessageComponent() {
    }
    SuccessMessageComponent.prototype.ngOnInit = function () {
    };
    __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Input"])(),
        __metadata("design:type", _models__WEBPACK_IMPORTED_MODULE_1__["SuccessMessage"])
    ], SuccessMessageComponent.prototype, "success", void 0);
    SuccessMessageComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-success-message',
            template: __webpack_require__(/*! ./success-message.component.html */ "./src/app/success-message/success-message.component.html"),
            styles: [__webpack_require__(/*! ./success-message.component.less */ "./src/app/success-message/success-message.component.less")]
        }),
        __metadata("design:paramtypes", [])
    ], SuccessMessageComponent);
    return SuccessMessageComponent;
}());



/***/ }),

/***/ "./src/app/upload-util.ts":
/*!********************************!*\
  !*** ./src/app/upload-util.ts ***!
  \********************************/
/*! exports provided: UploadFilter, UploadFilters, UploadValidator */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "UploadFilter", function() { return UploadFilter; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "UploadFilters", function() { return UploadFilters; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "UploadValidator", function() { return UploadValidator; });
var UploadFilter = /** @class */ (function () {
    function UploadFilter() {
    }
    return UploadFilter;
}());

var UploadFilters = /** @class */ (function () {
    function UploadFilters() {
    }
    UploadFilters.avatar = {
        "accept": ["image/png", "image/jpg", "image/jpeg", "image/gif"],
        "accept_ext": ["png", "jpg", "jpeg", "gif"],
        "size_limit": 262144,
    };
    UploadFilters.icon = {
        "accept": ["image/png", "image/jpg", "image/jpeg", "image/gif"],
        "accept_ext": ["png", "jpg", "jpeg", "gif"],
        "size_limit": 262144
    };
    return UploadFilters;
}());

var UploadValidator = /** @class */ (function () {
    function UploadValidator(filter) {
        this.filter = filter;
    }
    UploadValidator.prototype.check = function (file) {
        this.error = undefined;
        if (!file) {
            this.error = { msg: 'no file', detail: undefined };
            return false;
        }
        if (this.filter.accept_ext) {
            var accepted = false;
            var ext = file.name.split('.').pop();
            for (var _i = 0, _a = this.filter.accept_ext; _i < _a.length; _i++) {
                var accept_ext = _a[_i];
                if (accept_ext == ext) {
                    accepted = true;
                    break;
                }
            }
            if (!accepted) {
                this.error = { msg: 'invalid file extension', detail: undefined };
                return false;
            }
        }
        if (file.size > this.filter.size_limit) {
            this.error = { msg: 'size too big', detail: "File '" + file.name + "' has " + Math.round(file.size / 1024) + " KB" };
            return false;
        }
        return true;
    };
    return UploadValidator;
}());



/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// This file can be replaced during build by using the `fileReplacements` array.
// `ng build ---prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
var environment = {
    production: false
};
/*
 * In development mode, to ignore zone related error stack frames such as
 * `zone.run`, `zoneDelegate.invokeTask` for easier debugging, you can
 * import the following file, but please comment it out in production mode
 * because it will have performance impact when throw error
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm5/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");




if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(function (err) { return console.log(err); });


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /home/kelvin/IdeaProjects/submission/angular/src/main.ts */"./src/main.ts");


/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main.js.map