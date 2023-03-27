import requests

fname = input('Введите имя файла для чтения: ')

url = f'http://127.0.0.1:5000/{fname}'

# Отправляем GET-запрос на сервер, чтобы скачать файл
response = requests.get(url)

print(response.text)
