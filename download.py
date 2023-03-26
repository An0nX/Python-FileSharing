import requests

fname = input('Введите имя файла для скачивания: ')

url = f'http://127.0.0.1:5000/download/{fname}'

# Отправляем GET-запрос на сервер, чтобы скачать файл
response = requests.get(url)

# Сохраняем файл на диск
with open(fname, 'wb') as f:
    f.write(response.content)
