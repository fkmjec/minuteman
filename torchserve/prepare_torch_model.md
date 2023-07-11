# How to prepare a Torch model archive for summarization
* Create a handler file similar to the example `bart_model_serve.py`, 
* Download the model from HuggingFace using the transformers library and the `model_saver.py` script
* move the model to a file `pytorch_model.bin`
* to prepare the `.mar` file, run `torch-model-archiver --model-name [MODEL_NAME] --version 1.0 --serialized-file ./pytorch_model.bin --extra-files "./config.json,./generation_config.json,[POSSIBLE_OTHERS]" --handler "../[YOUR_HANDLER_FILE].py"`
* move it into a directory where you store Torch models
* when running torchserve, run `torchserve --start --model-store torch_model_dir/ --models bart=[MODEL_NAME].mar` while substituting the parameters for your current situation