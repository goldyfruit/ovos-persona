"""Only the primary language trains while the persona service loads; the rest
wait for their first query or for ``mycroft.ready``."""
import tempfile
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

from ovos_persona import PersonaService

CONFIG = {"lang": "en-US", "secondary_langs": ["fr-FR", "de-DE"]}


def _service(cache_dir):
    svc = PersonaService.__new__(PersonaService)
    svc.config = {"intent_cache": cache_dir}
    svc.intent_matchers = {}
    svc.untrained_langs = []
    with patch("ovos_persona.Configuration", return_value=CONFIG):
        svc.load_intent_files()
    return svc


class TestDeferredTraining(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.TemporaryDirectory()
        self.addCleanup(self.cache.cleanup)
        self.svc = _service(self.cache.name)

    def test_only_the_primary_language_trains_while_loading(self):
        self.assertFalse(self.svc.intent_matchers["en-US"].needs_compile)
        self.assertTrue(self.svc.intent_matchers["fr-FR"].needs_compile)
        self.assertTrue(self.svc.intent_matchers["de-DE"].needs_compile)
        self.assertEqual(sorted(self.svc.untrained_langs), ["de-DE", "fr-FR"])

    def test_an_untrained_language_still_matches_its_first_query(self):
        # a restart: the previous boot left every language's models cached
        for matcher in self.svc.intent_matchers.values():
            matcher.train()
        fr = _service(self.cache.name).intent_matchers["fr-FR"]
        self.assertTrue(fr.needs_compile)
        self.assertEqual(fr.calc_intent("liste les personas disponibles").name,
                         "list_personas.intent")

    def test_ready_trains_the_rest_in_the_background(self):
        with patch("ovos_persona.threading.Thread") as thread:
            self.svc.train_untrained_matchers(Message("mycroft.ready"))
            target = thread.call_args.kwargs["target"]
            self.assertTrue(thread.call_args.kwargs["daemon"])
        self.assertEqual(self.svc.untrained_langs, [])
        target()
        self.assertFalse(self.svc.intent_matchers["fr-FR"].needs_compile)
        self.assertFalse(self.svc.intent_matchers["de-DE"].needs_compile)


class TestReadyHook(unittest.TestCase):
    def test_the_service_trains_the_rest_on_ready(self):
        bus = FakeBus()
        calls = []

        def train(svc, message=None):
            calls.append(message.msg_type)

        # plain functions: workshop scans the class for decorated handlers,
        # and a MagicMock claims to be one
        with patch.object(PersonaService, "load_personas", lambda svc, path=None: None), \
                patch.object(PersonaService, "load_intent_files", lambda svc: None), \
                patch.object(PersonaService, "train_untrained_matchers", train):
            PersonaService(bus=bus, config={})
            bus.emit(Message("mycroft.ready"))
            bus.emit(Message("mycroft.ready"))
        self.assertEqual(calls, ["mycroft.ready"])


if __name__ == "__main__":
    unittest.main()
