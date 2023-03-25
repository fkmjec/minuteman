#!/usr/bin/env python3
import argparse
from datetime import datetime
import whisper
from pathlib import Path
import json
import shutil
import tempfile


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="whisper-base", help="the name of the resulting model")
    parser.add_argument("--model_type", type=str, default="base.en", help="the type of the whisper model being loaded")
    parser.add_argument("--model_dir", type=str, default="model_pt", help="the directory where the temp model is stored")
    parser.add_argument("--handler", type=str, default="transcribe_model_serve.py", help="the TorchServe handler file")
    args = parser.parse_args()
    return args

def copy_extra_files(extra_files, tmp_dir):
    """Copy extra files to tmp_dir. work with both folder and file"""
    for file in extra_files:
        if Path(file).is_dir():
            shutil.copytree(file, tmp_dir.joinpath(file))
        else:
            shutil.copy(file, tmp_dir.joinpath(file))

def main():
    args = parse()
    model_name = args.model_name
    model_type = args.model_type
    model_dir = args.model_dir
    handler = args.handler
    # create a temp in-memory dir with shutil
    with tempfile.TemporaryDirectory() as tmp_dir:
        print('created temporary directory', tmp_dir)
        tmp_dir = Path(tmp_dir)
            
        shutil.copy(handler, tmp_dir.joinpath(handler))

        _ = whisper.load_model(model_type, download_root=model_dir)

        manifest = {
            "createdOn": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "runtime": "python",
            "model": {
                "modelName": model_name,
                "serializedFile": "",
                "modelType": model_type,
                "modelDir": model_dir,
                "handler": args.handler,
                "modelVersion": "1.0"
            },
        }
        manifest_folder = tmp_dir.joinpath("MAR-INF")
        manifest_folder.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_folder.joinpath("MANIFEST.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)

        zipfile = shutil.make_archive(f"./model_store/{model_name}", 'zip', tmp_dir)
        zippath = Path(zipfile)
        marpath = zippath.rename(zippath.with_suffix(".mar"))
        print(f"Created MAR file: {marpath}")
    
if __name__ == '__main__':
    main()
