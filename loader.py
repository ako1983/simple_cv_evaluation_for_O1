import requests

url = "http://127.0.0.1:8002/evaluate"
file_path = "path_to_CV"

with open(file_path, "r") as f:
    cv_text = f.read()

payload = {"cv_text": cv_text}

response = requests.post(url, json=payload)

print(response.json())
