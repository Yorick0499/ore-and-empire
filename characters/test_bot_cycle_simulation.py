"""48-hour session simulation with ordinary services and no gameplay grants."""
from collections import Counter
from datetime import datetime,timedelta
from io import StringIO
import json,os,random
from pathlib import Path
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from .models import PlayerProfile,StorePurchase,MarketTrade,EconomicEntry
from .bot_personalities import PERSONAS,in_session
from .world_clock import POLISH_TIME
from .bots import tick_bot

class CycleSimulationTests(TestCase):
    def test_two_days_of_real_sessions_and_purchases(self):
        from .world_management import seed_clean_world
        seed_clean_world();call_command('run_bots',create=7,create_only=True,stdout=StringIO())
        bots=list(PlayerProfile.objects.filter(is_bot=True).order_by('pk'))
        start=datetime(2026,11,10,tzinfo=POLISH_TIME)
        for n,(bot,key) in enumerate(zip(bots,PERSONAS)):
            bot.bot_personality=key;bot.bot_session_shift=n*120
            bot.energy_updated_at=bot.health_updated_at=bot.mana_updated_at=start;bot.save()
        actions=Counter();by_persona={k:Counter() for k in PERSONAS};offline=Counter();failures=[]
        saved=random.getstate();random.seed(11092026)
        try:
            for step in range(576):
                now=start+timedelta(minutes=5*step)
                with patch('django.utils.timezone.now',return_value=now):
                    for bot in bots:
                        active=in_session(bot,now);action,ok=tick_bot(bot)
                        if not active:self.assertEqual(action,'offline');offline[bot.bot_personality]+=1
                        else:actions[action]+=1;by_persona[bot.bot_personality][action]+=1
                        if not ok:failures.append([step,bot.pk,action])
        finally:random.setstate(saved)
        facts={'kind':'sessions_48h','sampling_minutes':5,'population':7,'actions':dict(actions),'by_persona':{k:dict(v) for k,v in by_persona.items()},'offline_samples':dict(offline),'trades':MarketTrade.objects.count(),'purchases':StorePurchase.objects.count(),'simulated_shards':sum(EconomicEntry.objects.filter(operation='simulated_purchase').values_list('amount',flat=True)),'failures':failures,'limits':['Próbkowanie pięciominutowe nie mierzy minimalnych odstępów 15–120 sekund.','Mała populacja startowa nie stanowi prognozy długookresowej gospodarki.']}
        target=os.environ.get('ORE_PROBE_REPORT')
        if target:
            p=Path(target);rows=json.loads(p.read_text());rows.append(facts);p.write_text(json.dumps(rows,ensure_ascii=False))
        self.assertFalse(failures,failures[:10]);self.assertTrue(all(offline[k]>0 for k in PERSONAS))
        for action in ['mine','hunt','shop','adventure','adventure_claim']:self.assertGreater(actions[action],0,facts)
        self.assertGreater(facts['simulated_shards'],0);self.assertGreater(by_persona['patron']['shop'],0,facts)
        for bot in bots:
            bot.refresh_from_db();self.assertGreater(bot.experience,0);self.assertGreaterEqual(bot.premium_balance,0);self.assertGreaterEqual(bot.ore_balance,0)
