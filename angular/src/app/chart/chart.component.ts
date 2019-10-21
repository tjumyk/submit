import {AfterViewInit, Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from '@angular/core';
import Chart from 'chart.js';

@Component({
  selector: 'app-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.less']
})
export class ChartComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input()
  width: string = '100%';
  @Input()
  height: string = '20vh';
  @Input()
  data: any;

  @ViewChild('canvas')
  canvas: ElementRef;

  chart: Chart;

  constructor() { }

  ngOnInit() {
  }

  ngAfterViewInit(): void {
    if (!this.canvas.nativeElement || !this.data)
      return;
    this.chart = new Chart(this.canvas.nativeElement, this.data)
  }

  ngOnDestroy(): void {
    if(this.chart){
      this.chart.destroy();
      this.chart = undefined;
    }
  }

}
