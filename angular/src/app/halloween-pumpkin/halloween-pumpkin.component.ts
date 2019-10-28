import {AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild} from '@angular/core';

@Component({
  selector: 'app-halloween-pumpkin',
  templateUrl: './halloween-pumpkin.component.html',
  styleUrls: ['./halloween-pumpkin.component.less']
})
export class HalloweenPumpkinComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('pumpkin')
  pumpkin: ElementRef;

  laugh: HTMLAudioElement;
  creepy: HTMLAudioElement;

  laughTimeout;
  creepyTimeout;

  constructor(private element: ElementRef) {
  }

  ngOnInit() {
  }

  ngAfterViewInit(): void {
    if (!this.pumpkin || !this.pumpkin.nativeElement)
      return;

    const element = this.element.nativeElement;

    element.addEventListener('click', () => {
      if(element.classList.contains('active'))
        return;
      if(!this.laugh)
        this.laugh = new Audio('static/assets/laugh.mp3');
      if(!this.creepy)
        this.creepy = new Audio('static/assets/creepy.mp3');
      clearTimeout(this.laughTimeout);
      clearTimeout(this.creepyTimeout);
      element.classList.add('active');
      this.laughTimeout = setTimeout(() => {
        this.laugh.play();
      }, 3000);
      this.creepyTimeout = setTimeout(() => {
        this.creepy.play();
      }, 6000);
    });
    element.addEventListener('mouseleave', () => {
      element.classList.remove('active');
      this.reset();
    });
  }

  ngOnDestroy(): void {
    this.reset();
  }

  private reset(){
    clearTimeout(this.laughTimeout);
    clearTimeout(this.creepyTimeout);

    if(this.laugh){
      this.laugh.pause();
      this.laugh.currentTime = 0;
    }
    if(this.creepy){
      this.creepy.pause();
      this.creepy.currentTime = 0;
    }
  }
}
