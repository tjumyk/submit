import {AfterContentInit, Component, ContentChild, HostListener, OnDestroy, OnInit} from '@angular/core';
import Popper from "popper.js";
import {PopupContentComponent} from "../popup-content/popup-content.component";
import {PopupRefComponent} from "../popup-ref/popup-ref.component";

@Component({
  selector: 'app-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.less']
})
export class PopupComponent implements OnInit, OnDestroy, AfterContentInit {
  @ContentChild(PopupRefComponent)
  popRef: PopupRefComponent;

  @ContentChild(PopupContentComponent)
  popContent: PopupContentComponent;

  private enabled: boolean;

  get createPopup() {
    if (!this.popContent)
      return false;
    return this.popContent.create;
  };

  set createPopup(create: boolean) {
    if (this.popContent)
      this.popContent.create = create;
  }

  private popper: Popper;

  private showDelay: number = 100;
  private hideDelay: number = 100;

  private showPopTimeout: number;
  private hidePopTimeout: number;

  constructor() {
  }

  ngOnInit() {
  }

  ngAfterContentInit() {
    if (this.checkValid()) {
      this.enabled = true;
    }
  }

  ngOnDestroy(): void {
    clearTimeout(this.showPopTimeout);
    clearTimeout(this.hidePopTimeout);

    if (this.popper) {
      this.popper.destroy();
      this.popper = undefined;
    }
  }

  private checkValid(): boolean {
    if (!this.popRef || !this.popContent) {
      return false;
    }
    return true;
  }

  showPopup() {
    if (!this.enabled)
      return;

    if (!this.createPopup) {
      this.createPopup = true;

      setTimeout(() => {
        if (!this.createPopup)
          return;

        this.popper = new Popper(this.popRef.el.nativeElement, this.popContent.el.nativeElement, {
          placement: 'top-start'
        });
        setTimeout(() => {
          this.showPopupInternal();
        })
      })
    } else {
      this.showPopupInternal();
    }
  }

  private showPopupInternal() {
    if (!this.enabled || !this.popContent || !this.popper)
      return;

    const popCardElement = this.popContent.el.nativeElement;
    if (popCardElement.classList.contains('visible'))
      return;

    popCardElement.classList.add('loading');
    this.popper.update();
    popCardElement.classList.remove('loading');
    popCardElement.classList.add('visible');
  }

  hidePopup() {
    if (!this.enabled)
      return;

    if (this.popContent) {
      const popCardElement = this.popContent.el.nativeElement;
      if (popCardElement.classList.contains('visible')) {
        popCardElement.classList.remove('visible');
      }
    }

    if (this.popper) {
      this.popper.destroy();
      this.popper = undefined;
    }
    this.createPopup = false;
  }

  @HostListener('mouseenter') onStart() {
    if (!this.enabled)
      return;

    clearTimeout(this.hidePopTimeout);
    this.showPopTimeout = setTimeout(() => this.showPopup(), this.showDelay)
  }

  @HostListener('mouseleave') onEnd() {
    if (!this.enabled)
      return;

    clearTimeout(this.showPopTimeout);
    this.hidePopTimeout = setTimeout(() => this.hidePopup(), this.hideDelay)
  }

}
