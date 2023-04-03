from string import Formatter


class SystemMessage:
    def __init__(self, utterance):
        self.utterance = utterance


class UserMessage:
    def __init__(self, utterance):
        self.utterance = utterance


class LLMMessage:
    def __init__(self, utterance):
        self.utterance = utterance


class ChatHistory:
    def __init__(self, prompt_template, max_size=25, **kwargs):
        self.prompt_template = prompt_template
        self.variables = kwargs or {}
        self.max_size = max_size
        self.buffer = []

    def user_says(self, utterance):
        self._add_message(UserMessage(f"User: {utterance}"))

    def llm_says(self, utterance):
        self._add_message(LLMMessage(f"AI: {utterance}"))

    def _add_message(self, message):
        assert isinstance(message, UserMessage) or \
               isinstance(message, LLMMessage)
        self.buffer.append(message)
        if len(self.buffer) > 25:
            self.buffer = self.buffer[-25:]

    @property
    def prompt(self):
        kws = [fname for _, fname, _, _ in Formatter().parse(self.prompt_template) if fname]
        final_prompt = self.prompt_template.format(**{k: self.variables[k] for k in kws})
        for message in self.buffer:
            kws = [fname for _, fname, _, _ in Formatter().parse(message.utterance) if fname]
            utt = message.utterance.format(**{k: self.variables[k] for k in kws})
            final_prompt += f"\n{utt}"
        return final_prompt


class InstructionHistory:
    def __init__(self, prompt_template, max_size=5, **kwargs):
        self.prompt_template = prompt_template
        self.variables = kwargs or {}
        self.max_size = max_size
        self.buffer = []

    def instruct(self, instruction, data):
        if callable(data):
            data = data(instruction)  # remote data source
        if isinstance(data, dict):
            self.variables.update(data)
            data = "\n".join([f"{k}: {v}" for k, v in data.items()])
        self._add_message(SystemMessage(f"\n## INSTRUCTION\n\n{instruction}"))
        self._add_message(UserMessage(f"\n## DATA\n\n{data}"))

    def llm_says(self, response):
        self._add_message(LLMMessage(f"\n## RESPONSE\n\n{response}"))

    def _add_message(self, message):
        self.buffer.append(message)
        if len(self.buffer) > 25:
            self.buffer = self.buffer[-25:]

    @property
    def prompt(self):
        kws = [fname for _, fname, _, _ in Formatter().parse(self.prompt_template) if fname]
        final_prompt = self.prompt_template.format(**{k: self.variables[k] for k in kws})
        for message in self.buffer:
            kws = [fname for _, fname, _, _ in Formatter().parse(message.utterance) if fname]
            utt = message.utterance.format(**{k: self.variables[k] for k in kws})
            final_prompt += f"\n{utt}"
        return final_prompt



if __name__ == "__main__":
    c = ChatHistory("this assistant is {persona} and is called {name}", persona="evil", name="mycroft")
    c.user_says("hello!")
    c.llm_says("hello user")
    c.user_says("what is your name?")
    c.llm_says("my name is {name}")
    print(c.prompt)
    # this assistant is evil and is called mycroft
    # User: hello!
    # AI: hello user
    # User: what is your name?
    # AI: my name is mycroft

    def get_wolfram(query):
        return {"wolfram_answer": "42"}

    c = InstructionHistory("you are an AGI, follow the prompts")
    c.instruct("what is the speed of light", get_wolfram)
    print(c.variables) # {'wolfram_answer': '42'}
    c.llm_says("the answer is {wolfram_answer}")
    print(c.prompt)
    # you are an AGI, follow the prompts
    #
    # ## INSTRUCTION
    #
    # what is the speed of light
    #
    # ## DATA
    #
    # wolfram_answer: 42
    #
    # ## RESPONSE
    #
    # the answer is 42
