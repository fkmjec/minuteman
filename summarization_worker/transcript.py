import re

import kartik_utils
import text_utils


class Transcript:
    """
    The base class for all future processing. A transcript gets loaded into it from various formats and is then fed
    through preprocessing stages.
    """

    def __init__(self, roles, utterances):
        self.roles = roles
        self.utterances = utterances

    def kartik_clean(self):
        new_roles, new_utterances = [], []
        for role, utterance in zip(self.roles, self.utterances):
            if kartik_utils.check_context(utterance):
                utterance = kartik_utils.clean(kartik_utils.clean_punc(utterance))
                new_roles.append(role)
                new_utterances.append(utterance)
        self.roles = new_roles
        self.utterances = new_utterances

    def raw_str(self):
        joined_list = []
        for role, utterance in zip(self.roles, self.utterances):
            joined_list.append(role + ": " + utterance)
        return "\n".join(joined_list)

    def split_to_lens(self, tokenizer, max_len):
        splits = []
        current_split = ""
        current_len = 0
        for role, utterance in zip(self.roles, self.utterances):
            line = role + ": " + utterance
            tokenized = tokenizer.encode(line)
            if len(tokenized) > max_len:
                split_line = text_utils.split_to_lens(line, max_len, tokenizer)
                splits.extend(split_line)
            elif current_len + len(tokenized) > max_len:
                splits.append(current_split)
                current_split = ""
                current_len = 0
            else:
                current_split += "\n" + line
                current_len += len(tokenized)
        if current_len != 0:
            splits.append(current_split)
        return splits

    @staticmethod
    def from_gdoc(input_string):
        roles = []
        utterances = []
        utterance_start = re.compile("^\d\d:\d\d:\d\d - (.*):")
        current_utterance = ""
        current_role = ""

        for line in input_string.splitlines():
            match = utterance_start.match(line)
            if utterance_start.match(line) is not None:
                # start of new utterance
                roles.append(current_role)
                utterances.append(current_utterance)
                current_role = match.group(1)
                current_utterance = ""
            elif line.isspace():
                # let's not append empty lines into our utterances
                continue
            else:
                current_utterance += " " + line
        if current_utterance != "":
            roles.append(current_role)
            utterances.append(current_utterance)
        return Transcript(roles, utterances)

    @staticmethod
    def from_automin(input_string):
        roles = []
        utterances = []
        utterance_start = re.compile("^(\(.*\))(.*)$")
        current_utterance = ""
        current_role = ""

        for line in input_string.splitlines():
            match = utterance_start.match(line)
            if utterance_start.match(line) is not None:
                # start of new utterance
                if current_utterance != "" and current_role != "":
                    roles.append(current_role)
                    utterances.append(current_utterance)
                current_role = match.group(1)
                current_utterance = match.group(2)
            elif line.isspace():
                # let's not append empty lines into our utterances
                continue
            else:
                current_utterance += " " + line
        if current_utterance != "":
            roles.append(current_role)
            utterances.append(current_utterance)
        return Transcript(roles, utterances)
