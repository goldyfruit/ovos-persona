"""Only the primary language trains while the persona service loads; every
other language trains on its first query."""
import tempfile
import unittest
from unittest.mock import patch

from ovos_persona import IS_PADATIOUS, PersonaService

CONFIG = {"lang": "en-US", "secondary_langs": ["fr-FR", "de-DE"]}


def _service(cache_dir):
    svc = PersonaService.__new__(PersonaService)
    svc.config = {"intent_cache": cache_dir}
    svc.intent_matchers = {}
    with patch("ovos_persona.Configuration", return_value=CONFIG):
        svc.load_intent_files()
    return svc


@unittest.skipUnless(IS_PADATIOUS, "only a padatious container trains")
class TestDeferredTraining(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.TemporaryDirectory()
        self.addCleanup(self.cache.cleanup)
        self.svc = _service(self.cache.name)

    def test_only_the_primary_language_trains_while_loading(self):
        self.assertFalse(self.svc.intent_matchers["en-US"].needs_compile)
        self.assertTrue(self.svc.intent_matchers["fr-FR"].needs_compile)
        self.assertTrue(self.svc.intent_matchers["de-DE"].needs_compile)

    def test_an_untrained_language_still_matches_its_first_query(self):
        # a restart: the previous boot left every language's models cached
        for matcher in self.svc.intent_matchers.values():
            matcher.train()
        fr = _service(self.cache.name).intent_matchers["fr-FR"]
        self.assertTrue(fr.needs_compile)
        self.assertEqual(fr.calc_intent("liste les personas disponibles").name,
                         "list_personas.intent")
        self.assertFalse(fr.needs_compile)


if __name__ == "__main__":
    unittest.main()
