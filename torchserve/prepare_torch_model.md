# How to prepare a Torch model archive for TorchServe
So you want to add a new summarization model to Minuteman. This means you need to create a model `.mar` archive for TorchServe to accept. 
## Prerequisites
To be able to create the archive, you will need to have `torch-model-archiver installed`. It is available from `pip` and you can install it using
`pip install torch-model-archiver`. 
## Archive creation
First, create a handler file similar to the example `bart_model_serve.py`. Usually, you only need to alter the constant with the model name, but if you want to do something fancy in preprocessing, go for it. Notably, there is the possibility of quantization to be able to run larger models with less memory. This is exploited in our `flan_model_serve.py` handler file. 

First, download the selected model from HuggingFace using the `transformers` library, `pytorch` and the `model_saver.py` script. Or if you do not have `pytorch` installed, you can just download `pytorch_model.bin`, `generation_config.json` and `config.json` files from the Huggingface repositories manually.

To prepare the `.mar` archive containing the model, we run `torch-model-archiver --model-name [MODEL_NAME] --version 1.0 --serialized-file [path to pytorch_model.bin] --extra-files "[path to config.json],[path to generation_config.json]" --handler "[YOUR_HANDLER_FILE].py"`. Replace `[MODEL_NAME]` with the desired name of the archive and the other varibles with the paths of your downloaded model components. After running the command, you will be left with a `.mar` archive with the model.

## Using the archive in TorchServe
For usage, we need to move the created archive to the place where we store TorchServe models, namely `./torch_model_dir` in the project repository. In the `docker-compose.yml` file, you then specify the model and its name in the command to run torchserve like this: `torchserve --start --model-store torch_model_dir/ --models [NAME]=[MODEL_NAME].mar ...` while substituting the names and paths for your situation.