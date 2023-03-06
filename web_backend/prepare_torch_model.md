# How to prepare a Torch model at SLT
* to prepare the `.mar` file, run `torch-model-archiver --model-name [MODEL_NAME] --version 1.0 --serialized-file ./[MODEL_FILE].bin --extra-files "./config.json,./generation_config.json" --handler "../torch_model_serve.py"`
* move it into a directory where you store Torch models
* run `torchserve --start --model-store torch_model_dir/ --models bart=bart-large-xsum.mar` while substituting the parameters for your current situation