import requests
import json
import transformers

MODEL_CHECKPOINT = "facebook/bart-large-xsum"

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

text = input("Please type in a bit of text to summarize")
model_input = tokenizer(text)
model_input = dict(model_input)

rest_url = 'http://localhost:8501/v1/models/final_finetuned:predict'
json_data = {'signature_name': 'serving_default', 'instances': [dict_text]}

json_response = requests.post(rest_url, json=json_data)
pred = json.loads(json_response.text)
print(pred)
