import { Component, Input, OnInit } from '@angular/core';
import { AppService } from '../app.service'
import * as Highcharts from 'highcharts';

declare var require: any;
let Boost = require('highcharts/modules/boost');
let noData = require('highcharts/modules/no-data-to-display');
let More = require('highcharts/highcharts-more');

Boost(Highcharts);
noData(Highcharts);
More(Highcharts);
noData(Highcharts);

@Component({
  selector: 'app-live-analytics',
  templateUrl: './live-analytics.component.html',
  styleUrls: ['./live-analytics.component.css']
})
export class LiveAnalyticsComponent implements OnInit {

public options: any = {
    chart: {
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
        type: 'pie'
    },
    title: {
        text: 'Topic distribution of queries',
        align: 'left'
    },
    tooltip: {
        pointFormat: '<b>{point.percentage:.1f}%</b>'
    },
    accessibility: {
        point: {
            valueSuffix: '%'
        }
    },
    plotOptions: {
        pie: {
            allowPointSelect: true,
            cursor: 'pointer',
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {point.percentage:.1f} %'
            }
        }
    },
    series: [{
        name: 'Sentiment',
        colorByPoint: true,
        data: []
    }]
}
  public options2: any = {
    chart: {
        plotBackgroundColor: null,
        plotBorderWidth: null,
        plotShadow: false,
        type: 'pie'
    },
    title: {
        text: 'Sentiment distribution of queries',
        align: 'left'
    },
    tooltip: {
        pointFormat: '<b>{point.percentage:.1f}%</b>'
    },
    accessibility: {
        point: {
            valueSuffix: '%'
        }
    },
    plotOptions: {
        pie: {
            allowPointSelect: true,
            cursor: 'pointer',
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {point.percentage:.1f} %'
            }
        }
    },
    series: [{
        name: 'Sentiment',
        colorByPoint: true,
        data: []
    }]
}

  constructor(private appService: AppService) { }

  ngOnInit(){
    this.appService.stats().subscribe((response: any) =>{
      this.options.series[0].data = response.response;
      Highcharts.chart('container', this.options);
    })
    this.appService.sentiment_history().subscribe((response: any) =>{
      this.options2.series[0].data = response.response;
      Highcharts.chart('container1', this.options2);
    })
  }

}