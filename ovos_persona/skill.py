import os

from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.xdg_utils import xdg_data_home
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

        # choose default persona, filename without .json extension
        self.active_persona = self.settings.get("default_persona")

        self.add_event("ovos.persona.register", self.handle_register_persona)
        self.add_event("ovos.persona.deregister", self.handle_deregister_persona)
        self.add_event("ovos.persona.enable", self.handle_enable_persona)
        self.add_event("ovos.persona.disable", self.handle_disable_persona)
        self.register_fallback(self.ask_persona, 85)

    def handle_register_persona(self, message):
        name = message.data.get("name")
        persona = message.data.get("persona")
        self.persona.register_persona(name, persona)

    def handle_deregister_persona(self, message):
        name = message.data.get("name")
        self.persona.deregister_persona(name)

    def handle_enable_persona(self, message):
        name = message.data.get("name")
        self.active_persona = name  # TODO Session support

    def handle_disable_persona(self, message):
        self.active_persona = None

    def ask_persona(self, message):
        if self.active_persona is None:
            return False
        utterance = message.data['utterance']
        answer = self.persona.chatbox_ask(utterance, self.active_persona, self.lang)
        if not answer:
            return False
        self.speak(answer)
        return True
