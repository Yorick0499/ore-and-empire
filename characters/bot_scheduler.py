"""Cooperative local scheduler: one resident between HTTP requests, no catch-up waves."""
from collections import deque
import time


class BotScheduler:
    def __init__(self, interval=5, clock=time.monotonic):
        self.interval=interval
        self.clock=clock
        self.queue=deque()
        self.next_tick=clock()
        self.rest_until={}
        self.cost_ema=0.0

    def population(self, ids):
        ids=set(ids)
        retained=[pk for pk in self.queue if pk in ids]
        self.queue=deque(retained+sorted(ids-set(retained)))
        self.rest_until={pk:deadline for pk,deadline in self.rest_until.items() if pk in ids}

    @property
    def gap(self):
        # At most five actions/s and an adaptive ~20% scheduler duty cycle.
        # This is a pacing target, not a hard CPU quota for expensive individual turns.
        return max(.2,self.interval/max(1,len(self.queue)),4*self.cost_ema)

    def timeout(self):
        return min(1,max(0,self.next_tick-self.clock())) if self.queue else 1

    def step(self, tick):
        now=self.clock()
        if now<self.next_tick or not self.queue:return None
        selected=None
        for _ in range(len(self.queue)):
            pk=self.queue.popleft();self.queue.append(pk)
            if now>=self.rest_until.get(pk,0):selected=pk;break
        if selected is None:
            self.next_tick=min(self.rest_until.values());return None
        start=self.clock()
        result=tick(selected)
        elapsed=max(0,self.clock()-start)
        self.cost_ema=elapsed if not self.cost_ema else .8*self.cost_ema+.2*elapsed
        if result and result[0]=='wait':self.rest_until[selected]=self.clock()+30
        self.next_tick=self.clock()+self.gap
        return selected,result
