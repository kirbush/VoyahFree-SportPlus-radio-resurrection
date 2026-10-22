package ru.local.voyah.fmloader;
public class TestRetrySchedule {
 public static void main(String[] args){
  RetrySchedule r=new RetrySchedule();
  if(!r.shouldAttempt(0))throw new AssertionError("initial start");
  r.failed(0);if(r.shouldAttempt(29999)||!r.shouldAttempt(30000))throw new AssertionError("first retry");
  r.failed(30000);r.failed(60000);
  if(r.shouldAttempt(179999)||!r.shouldAttempt(180000))throw new AssertionError("late root bootstrap must retry");
  for(long now=180000;now<1800000;now+=120000){if(!r.shouldAttempt(now))throw new AssertionError("permanent retry lockout");r.failed(now);}
  r.reset();if(r.failures()!=0||!r.shouldAttempt(1800000))throw new AssertionError("explicit retry reset");
  System.out.println("PASS boot root delay and long outage retry without permanent lockout");
 }
}
