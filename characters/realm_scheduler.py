"""One adaptive queue for all realms, with a separate fenced owner per realm."""
from itertools import zip_longest
from time import monotonic
from .models import World
from .realms import open_worlds,world_scope
from .scheduler_lease import SchedulerGuard
from .bot_personalities import due_population

class ParallelRealms:
    def __init__(self):
        self.guards = {}
        self.next_arrival_check = None
    def sync(self,primary,cleanup):
        opened=list(open_worlds().filter(configured=True).exclude(pk=primary.world_id))
        wanted={w.pk for w in opened}|{primary.world_id}
        for pk in list(self.guards):
            if pk not in wanted:self.guards.pop(pk).release()
        for world in opened:
            if world.pk not in self.guards:
                guard=SchedulerGuard(world).acquire();self.guards[world.pk]=guard;cleanup.callback(guard.release)
            with self.guards[world.pk].work():pass
        self.guards[primary.world_id]=primary
        now = monotonic()
        if self.next_arrival_check is None or now >= self.next_arrival_check:
            from .bot_arrivals import admit_next_cohort
            admit_next_cohort(primary)
            self.next_arrival_check = now + 30
        from django.db.models import Q
        worlds = open_worlds().filter(Q(configured=True) | Q(pk=primary.world_id)).order_by('pk')
        populations = [due_population(world) for world in worlds]
        return [pk for band in zip_longest(*populations) for pk in band if pk is not None]
    def for_profile(self,profile):return self.guards[profile.world_id]
    def events(self):
        from .world_events import ensure_world_events
        for world in World.objects.filter(pk__in=self.guards):
            with world_scope(world),self.guards[world.pk].work():ensure_world_events()
