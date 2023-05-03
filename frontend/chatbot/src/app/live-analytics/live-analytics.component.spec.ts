import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LiveAnalyticsComponent } from './live-analytics.component';

describe('LiveAnalyticsComponent', () => {
  let component: LiveAnalyticsComponent;
  let fixture: ComponentFixture<LiveAnalyticsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ LiveAnalyticsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LiveAnalyticsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
