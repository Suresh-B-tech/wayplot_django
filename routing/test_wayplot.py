# import requests

# # Upload GPX
# url_upload = "http://127.0.0.1:8000/routing/upload-gpx/"
# files = {'file': open(r'D:\wayplot\campus.gpx', 'rb')}
# response = requests.post(url_upload, files=files)
# print("Upload response:", response.json())

# # Get path
# url_path = "http://127.0.0.1:8000/routing/path/"
# params = {"start": 0, "end": 50, "mode": "shortest"}
# response = requests.get(url_path, params=params)
# print("Path response:", response.json())

import requests

url_upload = "http://127.0.0.1:8000/routing/upload-gpx/"
files = {'file': open(r'D:\wayplot\campus.gpx', 'rb')}

response = requests.post(url_upload, files=files)

print("Status code:", response.status_code)
print("Response text:", response.text)

