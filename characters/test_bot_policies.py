import json,time,threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import SimpleTestCase,TestCase
from .bots import Observation,BaselinePolicyV18,tick_bot
from .bot_policies import OllamaPolicy,candidates,replay,Budget
from .models import BotDecision,BotPolicyBudget
from .scheduler_lease import SchedulerGuard

class LocalPolicyTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                cls.requests.append(body)
                if cls.redirect:
                    self.send_response(302);self.send_header("Location","https://example.invalid/private");self.end_headers();return
                if cls.delay:time.sleep(cls.delay)
                payload=cls.reply
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
                try:self.wfile.write(payload)
                except (BrokenPipeError,ConnectionResetError):pass
            def log_message(self,*args):pass
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();super().tearDownClass()
    def setUp(self):
        self.__class__.requests=[];self.__class__.delay=0;self.__class__.redirect=False
        self.__class__.reply=json.dumps({'message':{'content':'{"choice":1}'},'prompt_eval_count':100,'eval_count':8}).encode()
        self.obs=Observation(100,20,False,False,None,None,None,None,True,health=50,max_health=50,hunt_key='young_scavenger')
        self.endpoint=f'http://127.0.0.1:{self.server.server_port}/api/chat'
    def policy(self,**kw):return OllamaPolicy('local-test',endpoint=self.endpoint,timeout=2,**kw)
    def test_local_output_is_mapped_to_allowlist_and_contains_no_identity(self):
        policy=self.policy();chosen=policy.choose(self.obs)
        self.assertEqual(chosen,candidates(self.obs)[1]);self.assertEqual(policy.last_details['status'],'accepted')
        request=self.requests[0]
        self.assertEqual(request['options']['num_gpu'],0)
        self.assertNotIn('username',json.dumps(request));self.assertNotIn('password',json.dumps(request));self.assertFalse(settings_secret() in json.dumps(request),'Private setting leaked')
    def test_transport_gets_no_database_or_authentication_environment(self):
        from types import SimpleNamespace
        with patch.dict('os.environ',{'PGPASSWORD':'synthetic-private','SECRET_KEY':'synthetic-private','DATABASE_URL':'synthetic-private'}),patch('characters.bot_policies.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=b'{"choice":0,"prompt_tokens":1,"generated_tokens":1}')) as run:
            self.policy().choose(self.obs)
        self.assertTrue({'PGPASSWORD','SECRET_KEY','DATABASE_URL'}.isdisjoint(run.call_args.kwargs['env']))
    def test_endpoint_cannot_redirect_observations_elsewhere(self):
        self.__class__.redirect=True
        policy=self.policy();self.assertEqual(policy.choose(self.obs),candidates(self.obs)[0]);self.assertEqual(policy.last_details['status'],'fallback')
    def test_invalid_choices_extra_fields_and_oversized_reply_fall_back(self):
        for output in ['{"choice":999}','{"choice":true}','{"choice":0,"action":"admin"}','not json']:
            self.__class__.reply=json.dumps({'message':{'content':output}}).encode()
            policy=self.policy();self.assertEqual(policy.choose(self.obs),BaselinePolicyV18().choose(self.obs));self.assertEqual(policy.last_details['status'],'fallback')
        self.__class__.reply=b'x'*5000;policy=self.policy();self.assertEqual(policy.choose(self.obs),candidates(self.obs)[0])
    def test_hard_deadline_and_circuit_breaker(self):
        self.__class__.delay=1
        policy=OllamaPolicy('local-test',endpoint=self.endpoint,timeout=.2)
        start=time.monotonic();self.assertEqual(policy.choose(self.obs),candidates(self.obs)[0]);self.assertLess(time.monotonic()-start,1)
        self.assertEqual(policy.choose(self.obs),candidates(self.obs)[0]);self.assertEqual(policy.last_details['status'],'budget-or-cooldown')
    def test_call_and_token_limits_stop_transport(self):
        policy=self.policy(max_calls=1)
        policy.choose(self.obs);policy.choose(self.obs);self.assertEqual(len(self.requests),1)
        self.assertEqual(policy.last_details['status'],'budget-or-cooldown')
        policy=self.policy(max_tokens=0);policy.choose(self.obs);self.assertEqual(len(self.requests),1)
    def test_forced_story_and_rewards_never_reach_model(self):
        policy=self.policy()
        for obs in (replace(self.obs,reward_ready=True),replace(self.obs,busy=True),replace(self.obs,story_action='story_accept',story_target=1)):
            self.assertEqual(policy.choose(obs),BaselinePolicyV18().choose(obs))
        self.assertEqual(self.requests,[])
    def test_remote_and_cloud_models_are_refused(self):
        for endpoint in ('https://remote.example/api/chat','http://127.0.0.1:11434/other','http://secret@localhost:11434/api/chat'):
            with self.assertRaises(ValueError):OllamaPolicy('local-test',endpoint=endpoint)
        with self.assertRaises(ValueError):OllamaPolicy('some-cloud')
    def test_replay_never_requeries_model_and_detects_changed_proof(self):
        policy=self.policy();action,target=policy.choose(self.obs)
        from types import SimpleNamespace
        from dataclasses import asdict
        row=SimpleNamespace(observation=asdict(self.obs),policy_snapshot=policy.last_details,action=action,target_id=target)
        self.assertTrue(replay(row)['matches']);self.assertEqual(len(self.requests),1)
        row.policy_snapshot={**row.policy_snapshot,'choice':999};self.assertFalse(replay(row)['supported'])

def settings_secret():
    from django.conf import settings
    return settings.SECRET_KEY

class PersistentPolicyBudgetTests(TestCase):
    def test_budget_survives_policy_restart_and_stale_owner_cannot_spend(self):
        user=User.objects.create_user('budget-test');world=user.playerprofile.world
        with SchedulerGuard(world) as guard:
            first=Budget(1,5000,5000,guard);self.assertTrue(first.reserve(1000,1000))
            restarted=Budget(1,5000,5000,guard);self.assertFalse(restarted.reserve(1000,1000))
            first.cooldown();row=BotPolicyBudget.objects.get(world=world);self.assertIsNotNone(row.blocked_until)
            self.assertEqual(row.calls,1)
        from .scheduler_lease import LeaseLost
        with self.assertRaises(LeaseLost):first.reserve(1,1)
    def test_worker_default_is_rules_and_telemetry_supports_local_replay(self):
        from .bot_policies import configured_policy
        with patch.dict('os.environ',{'ORE_BOT_POLICY':'rules'}):self.assertIsNone(configured_policy(None))

    def test_actual_bot_action_records_versioned_local_policy_snapshot(self):
        from .bot_telemetry import replay_decision
        call_command('seed_world',stdout=StringIO())
        bot=User.objects.create_user('local-policy-bot').playerprofile;bot.is_bot=True;bot.bot_role='miner';bot.save()
        policy=OllamaPolicy('unused-local-model',endpoint='http://127.0.0.1:9/api/chat')
        self.assertEqual(tick_bot(bot,policy, force_active=True),('mine',True))
        record=BotDecision.objects.get(profile=bot)
        self.assertEqual(record.policy_version,'ollama-1');self.assertEqual(record.schema_version,19)
        self.assertEqual(record.policy_snapshot['status'],'forced-rules');self.assertTrue(replay_decision(record)['matches'])
