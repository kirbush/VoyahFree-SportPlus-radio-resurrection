package ru.local.voyah.fmloader;
/** Monotonic backoff; boot-time root/USB delays must not permanently disable FM. */
final class RetrySchedule {
 private int failures; private long next;
 synchronized boolean shouldAttempt(long now){return now>=next;}
 synchronized long failed(long now){failures++;long delay=failures<3?30000:120000;next=now+delay;return delay;}
 synchronized int failures(){return failures;}
 synchronized void reset(){failures=0;next=0;}
}
