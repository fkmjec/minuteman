from transformers import TFBartForConditionalGeneration, TFT5ForConditionalGeneration, BartForConditionalGeneration
import tensorflow as tf

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--from_path", type=str, help="where to load the model from")
parser.add_argument("--save_to", type=str, help="where to save the resulting model for tf serving")

# Creation of a subclass in order to define a new serving signature
class BartGenerationModel(TFBartForConditionalGeneration):
    # Decorate the serving method with the new input_signature
    # an input_signature represents the name, the data type and the shape of an expected input
    # @tf.function(input_signature=[{
    #     "input_ids": tf.TensorSpec((None, None), tf.int32, name="input_ids"),
    # }])
    # def generate_output(self, inputs):
    #     # TODO: include tokenizer here?
    #     output = self.generate(inputs["input_ids"])
    #     return output
    
    @tf.function(input_signature=[{
        "input_ids": tf.TensorSpec((None, None), tf.int32, name="input_ids"),
        "attention_mask": tf.TensorSpec((None, None), tf.int32, name="attention_mask"),
    }])
    def serving(self, inputs):
        # call the model to process the inputs
        output = self.generate(inputs["input_ids"], attention_mask=inputs["attention_mask"])

        # return the formated output
        return self.serving_output(output)

class T5GenerationModel(TFT5ForConditionalGeneration):
    @tf.function(input_signature=[{
        "input_ids": tf.TensorSpec((None, None), tf.int32, name="input_ids"),
        "attention_mask": tf.TensorSpec((None, None), tf.int32, name="attention_mask"),
    }])
    def serving(self, inputs):
        # call the model to process the inputs
        output = self.generate([inputs["input_ids"], inputs["attention_mask"]])

        # return the formated output
        return self.serving_output(output)



if __name__ == "__main__":
    args = parser.parse_args()
    # Instantiate the model with the new serving method
    print("loading model...")
    model = BartForConditionalGeneration.from_pretrained(args.from_path)
    print("saving model with a different signature...")
    model.save_pretrained(args.save_to)

