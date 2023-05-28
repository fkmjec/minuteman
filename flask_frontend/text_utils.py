import re
import logging

logger = logging.getLogger(__name__)

SEPARATORS = "\n"
TRSC_SEPARATOR = "\n-----TRANSCRIPT SEPARATOR-----\n"

def split_to_lens(input_str, max_len, tokenizer):
    splits = re.split(SEPARATORS, input_str)
    output = [""]
    current_output_len = 0
    j = 0
    for utterance in splits:
        tokenized_utterance = tokenizer.encode(utterance)
        assert len(tokenized_utterance) <= max_len
        if current_output_len + len(tokenized_utterance) <= max_len:
            output[j] += utterance
            current_output_len += len(tokenized_utterance)
        else:
            j += 1
            output.append("")
            output[j] += utterance
            current_output_len = len(tokenized_utterance)
    return output


def split_by_trsc_separator(input_str):
    splits = input_str.split(TRSC_SEPARATOR)
    splits = list(filter(lambda x: x != "", splits))
    return splits