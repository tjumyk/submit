import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild
} from '@angular/core';

@Component({
  selector: 'app-modal',
  templateUrl: './modal.component.html',
  styleUrls: ['./modal.component.less']
})
export class ModalComponent implements OnInit, OnDestroy, AfterViewInit {
  _show: boolean;
  shown: boolean;

  @Input() get show() {
    return this._show;
  }

  set show(show: boolean) {
    clearTimeout(this.showTracker);
    this.showTracker = setTimeout(() => {
      this.shown = show;
    }, this.animationDuration);
    this._show = show;
    this.showChange.emit(show);
  }

  @Output() showChange: EventEmitter<boolean> = new EventEmitter();

  @Input() animationDuration: number = 500; // milliseconds
  @Input() modalClass: string;
  @Input() dimmerClickClose: boolean = false;

  @ViewChild('modal')
  modalElement: ElementRef;

  private showTracker: number;

  constructor() {
  }

  ngOnInit() {
  }

  ngOnDestroy(): void {
    clearTimeout(this.showTracker);
  }

  ngAfterViewInit(): void {
    if (this.modalClass) {
      let classes = this.modalClass.trim();
      if (classes.length > 0) {
        this.modalElement.nativeElement.classList.add(...classes.split(/\s+/))
      }
    }
  }

  dimmerClicked(event: MouseEvent, dimmer: HTMLElement) {
    if (this.dimmerClickClose && event.target == dimmer) {
      this.show = false;
      event.stopImmediatePropagation();
    }
  }
}
