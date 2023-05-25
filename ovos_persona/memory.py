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


class _History:
    def __init__(self, prompt_template, prompt="A:", antiprompt="Q:",
                 max_size=25, **kwargs):
        self.prompt_str = prompt
        self.antiprompt_str = antiprompt
        self.prompt_template = prompt_template
        self.variables = kwargs or {}
        self.max_size = max_size

    def _fmt_vars(self, utterance):
        kws = [fname for _, fname, _, _ in Formatter().parse(utterance) if fname]
        return utterance.format(**{k: self.variables[k] for k in kws})

    @property
    def base_prompt(self):
        prompt = self._fmt_vars(self.prompt_template)
        return prompt

    def get_prompt(self, question):
        if isinstance(question, UserMessage):
            question = question.utterance
        final_prompt = self.base_prompt
        final_prompt += f"\n{self.antiprompt_str} {question}"
        final_prompt += f"\n{self.prompt_str} "
        return final_prompt


class ChatHistory(_History):
    def __init__(self, prompt_template, prompt="A:", antiprompt="Q:",
                 max_size=25, **kwargs):
        super().__init__(prompt_template, prompt, antiprompt, max_size, **kwargs)
        self.buffer = []

    @property
    def base_prompt(self):
        prompt = self._fmt_vars(self.prompt_template)
        for question, answer in self.buffer:
            q = self._fmt_vars(question.utterance)
            prompt += f"\n{self.antiprompt_str} {q}"
            a = self._fmt_vars(answer.utterance)
            prompt += f"\n{self.prompt_str} {a}"
        return prompt

    def add_qa(self, question, answer):
        if isinstance(question, str):
            question = UserMessage(question)
        if isinstance(answer, str):
            answer = LLMMessage(answer)
        self.buffer.append((question, answer))
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-1 * self.max_size:]


class InstructionHistory(_History):

    def __init__(self, prompt_template, prompt="## RESPONSE\n\n",
                 antiprompt="## INSTRUCTION\n\n", max_size=25, **kwargs):
        super().__init__(prompt_template, prompt, antiprompt, max_size, **kwargs)
        self.buffer = []

    @property
    def base_prompt(self):
        prompt = self._fmt_vars(self.prompt_template)
        for instruction, data, answer in self.buffer:
            q = self._fmt_vars(instruction.utterance)
            if data.utterance:
                q += f"\n\n##VARIABLES\n\n{self._fmt_vars(data.utterance)}\n"

            prompt += f"\n{self.antiprompt_str} {q}"
            a = self._fmt_vars(answer.utterance)
            prompt += f"\n{self.prompt_str} {a}"
        return prompt

    def instruct(self, instruction, data, answer):
        if callable(data):
            data = data(instruction)  # remote data source
        if isinstance(data, dict):
            self.variables.update(data)
            data = "\n".join([f"{k}: {v}" for k, v in data.items()])
        self.add_instruction(instruction, data, answer)

    def add_instruction(self, instruction, data, answer):
        if isinstance(instruction, str):
            instruction = SystemMessage(instruction)
        if isinstance(data, str):
            data = UserMessage(data)
        if isinstance(answer, str):
            answer = LLMMessage(answer)
        self.buffer.append((instruction, data, answer))
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-1 * self.max_size:]



if __name__ == "__main__":
    c = ChatHistory("this assistant is {persona} and is called {name}", persona="evil", name="mycroft")
    c.add_qa("hello!", "hello user")
    c.add_qa("what is your name?", "my name is {name}")
    print(c.base_prompt)
    # this assistant is evil and is called mycroft
    # User: hello!
    # AI: hello user
    # User: what is your name?
    # AI: my name is mycroft

    def get_wolfram(query):
        return {"wolfram_answer": "42"}

    c = InstructionHistory("you are an AGI, follow the prompts")
    c.instruct("what is the speed of light", get_wolfram, "the answer is {wolfram_answer}")
   # print(c.variables) # {'wolfram_answer': '42'}
    print(c.base_prompt)
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
