import argparse

from transformers import AutoModelForSeq2SeqLM

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name",
    type=str,
    required=True,
    help="The model name, for example facebook/bart-large-xsum",
)
parser.add_argument(
    "--save_to", type=str, required=True, help="where to save the resulting model"
)


if __name__ == "__main__":
    args = parser.parse_args()
    # Instantiate the model with the new serving method
    print("loading model...")
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name)
    print("saving model...")
    model.save_pretrained(args.save_to)
