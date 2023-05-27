import os

from ovos_utils import classproperty
from ovos_utils.intents import IntentBuilder
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.xdg_utils import xdg_data_home
from ovos_workshop.decorators import intent_handler, adds_context, removes_context
from ovos_workshop.skills.fallback import FallbackSkill

from ovos_persona import PersonaService


class PersonaSkill(FallbackSkill):

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=False,
                                   network_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=False,
                                   requires_gui=False,
                                   no_internet_fallback=True,
                                   no_network_fallback=True,
                                   no_gui_fallback=True)

    def initialize(self):
        # add persona .json files here
        personas_folder = f"{xdg_data_home()}/personas"
        os.makedirs(personas_folder, exist_ok=True)
        self.persona = PersonaService(personas_folder)
        self.active_persona = None

        self.add_event("ovos.persona.register", self.handle_register_persona)
        self.add_event("ovos.persona.deregister", self.handle_deregister_persona)
        self.add_event("ovos.persona.enable", self.handle_enable_persona)
        self.add_event("ovos.persona.disable", self.handle_disable_persona)
        self.add_event("ovos.persona.ask", self.handle_ask_persona)

        self.register_fallback(self.ask_persona, 85)

    # bus api
    def handle_register_persona(self, message):
        name = message.data.get("name")
        persona = message.data.get("persona")
        self.persona.register_persona(name, persona)

    def handle_deregister_persona(self, message):
        name = message.data.get("name")
        self.persona.deregister_persona(name)

    @adds_context("ActivePersona")
    def handle_enable_persona(self, message):
        self.active_persona = message.data.get("name")  # TODO Session support (from context)

    @removes_context("ActivePersona")
    def handle_disable_persona(self, message):
        self.active_persona = None

    def handle_ask_persona(self, message):
        utterance = message.data['utterance']
        answer = self.persona.chatbox_ask(utterance, self.active_persona, self.lang)
        self.bus.emit(message.response(data={"utterance": answer, "lang": self.lang}))

    # intents
    # NB: adapt intents requiring ActivePersona keyword,
    #     that keyword is virtual, it is only set/removed in converse method
    @intent_handler("summon.intent")
    def handle_summon_persona(self, message):
        self.handle_enable_persona(message)

    @intent_handler(IntentBuilder("ReleasePersona")
                    .require("ActivePersona")
                    .require("Release"))
    def handle_release_persona(self, message):
        self.handle_disable_persona(message)

    # converse
    def handle_deactivate(self, message):
        """ skill is no longer considered active by the intent service
        converse method will not be called, skills might want to reset state here
        """
        if self.active_persona:
            LOG.info(f"converse timed out, deactivating: {self.active_persona}")
            self.handle_disable_persona(message)

    def converse(self, message=None):
        if self.active_persona:
            # TODO - match handle_release_persona intent
            #
            return self.ask_persona(message)
        return False

    # fallback
    def ask_persona(self, message):
        persona = self.active_persona or self.settings.get("default_persona")
        if persona is None:
            return False
        utterance = message.data['utterance']
        answer = self.persona.chatbox_ask(utterance, persona, self.lang)
        if not answer:
            return False
        self.speak(answer)
        return True
