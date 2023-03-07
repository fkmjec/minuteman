import re

SEPARATORS = "\."

def split_to_lens(input_str, max_len, tokenizer):
    splits = re.split(SEPARATORS, input_str)
    output = [""]
    current_output_len = 0
    j = 0
    for sentence in splits:
        tokenized_sentence = tokenizer.encode(sentence)
        assert len(tokenized_sentence) <= max_len
        if current_output_len + len(tokenized_sentence) <= max_len:
            output[j] += sentence
            current_output_len += len(tokenized_sentence)
        else:
            j += 1
            output.append("")
            output[j] += sentence
            current_output_len = len(tokenized_sentence)

    return output
