from transformers import TFAutoModelForSeq2SeqLM
import tensorflow as tf

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--from_path", type=str, help="where to load the model from")
parser.add_argument("--save_to", type=str, help="where to save the resulting model for tf serving")

# Creation of a subclass in order to define a new serving signature
class ModifiedModel(TFAutoModelForSeq2SeqLM):
    # Decorate the serving method with the new input_signature
    # an input_signature represents the name, the data type and the shape of an expected input
    @tf.function(input_signature=[{
        "inputs_ids": tf.TensorSpec((None, None), tf.int64, name="input_ids"),
    }])
    def serving(self, inputs):
        # call the model to process the inputs
        output = self.generate(inputs["input_ids"])

        # return the formated output
        return self.serving_output(output)

if __name__ == "__main__":
    args = parser.parse_args()
    # Instantiate the model with the new serving method
    print("loading model...")
    model = ModifiedModel.from_pretrained("facebook/bart-large-xsum")
    print("saving model with a different signature...")
    model.save("bart-large-xsum", save_format="tf")

