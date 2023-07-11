from transformers import AutoModelForSeq2SeqLM

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--from_path", type=str, help="where to load the model from")
parser.add_argument("--save_to", type=str, help="where to save the resulting model")


if __name__ == "__main__":
    args = parser.parse_args()
    # Instantiate the model with the new serving method
    print("loading model...")
    model = AutoModelForSeq2SeqLM.from_pretrained(args.from_path)
    print("saving model...")
    model.save_pretrained(args.save_to)

