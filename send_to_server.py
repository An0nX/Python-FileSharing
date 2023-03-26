import requests

url = 'http://127.0.0.1:5000/load'

# Путь к файлу, который нужно отправить на сервер
file_path = r"".join(input("Введите путь к файлу: "))

# Открываем файл и отправляем его на сервер
with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

try:
    # Печатаем ссылку на загруженный файл
    print(response.json()['file_link'])
except KeyError:
    print(response.json()['error'])
