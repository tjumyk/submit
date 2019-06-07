import {AfterViewInit, Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {User} from "../models";
import Popper from "popper.js";

@Component({
  selector: 'app-user-mini-card',
  templateUrl: './user-mini-card.component.html',
  styleUrls: ['./user-mini-card.component.less']
})
export class UserMiniCardComponent implements OnInit, OnDestroy {
  @Input()
  user: User;

  @Input()
  enablePopup: boolean = false;

  @Input()
  enableAdmin: boolean = false;

  createPopup: boolean = false;

  @ViewChild('popRef')
  popRef: ElementRef;

  @ViewChild('popCard')
  popCard: ElementRef;

  @ViewChild('avatar')
  avatar: ElementRef;

  private popper: Popper;

  private showDelay: number = 100;
  private hideDelay: number = 100;

  private showPopTimeout: number;
  private hidePopTimeout: number;

  constructor() { }

  ngOnInit() {
  }

  ngOnDestroy(): void {
    clearTimeout(this.showPopTimeout);
    clearTimeout(this.hidePopTimeout);

    if(this.popper){
      this.popper.destroy();
      this.popper = undefined;
    }
  }

  showPopup(){
    if(!this.enablePopup)
      return;

    if(!this.createPopup){
      this.createPopup = true;

      setTimeout(()=>{
        if(!this.createPopup)
          return;

        this.popper = new Popper(this.popRef.nativeElement, this.popCard.nativeElement, {
          placement: 'top-start'
        });
        setTimeout(()=>{
          this.showPopupInternal();
        })
      })
    }else{
      this.showPopupInternal();
    }
  }

  private showPopupInternal(){
    if(!this.enablePopup || !this.popCard || !this.popper)
      return;

    const popCardElement = this.popCard.nativeElement;
    if(popCardElement.classList.contains('visible'))
      return;

    popCardElement.classList.add('loading');
    this.popper.update();
    popCardElement.classList.remove('loading');
    popCardElement.classList.add('visible');
  }

  hidePopup(){
    if(!this.enablePopup)
      return;

    if(this.popCard){
      const popCardElement = this.popCard.nativeElement;
      if(popCardElement.classList.contains('visible')){
        popCardElement.classList.remove('visible');
      }
    }

    if(this.popper){
      this.popper.destroy();
      this.popper = undefined;
    }
    this.createPopup = false;
  }

  onStart(){
    if(!this.enablePopup)
      return;

    clearTimeout(this.hidePopTimeout);
    this.showPopTimeout = setTimeout(()=>this.showPopup(), this.showDelay)
  }

  onEnd(){
    if(!this.enablePopup)
      return;

    clearTimeout(this.showPopTimeout);
    this.hidePopTimeout = setTimeout(()=>this.hidePopup(), this.hideDelay)
  }

}
