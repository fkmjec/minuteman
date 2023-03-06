import requests

MODEL_CHECKPOINT = "facebook/bart-large-xsum"

# tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

model_input = input("Please type in a bit of text to summarize: ")


rest_url = 'http://localhost:8080/predictions/bart'
files = {'model_input': ('model_input.txt', model_input)}
response = requests.post(rest_url, files=files)

print(response)
