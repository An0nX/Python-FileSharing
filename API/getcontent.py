import requests
from json.decoder import JSONDecodeError

fname = input('Введите имя файла для чтения: ')

url = input("Ссылка для загрузки: ")

response = requests.get(f'{url}/config').json()['lock_get_file']

# Отправляем GET-запрос на сервер, чтобы скачать файл
if response:
    response = requests.get(f'{url}/{fname}', params={'key': input('Введите пароль: ')})
else:
    response = requests.get(f'{url}/{fname}')

try:
    print(f'\nОшибка: {response.json()["error"]}\n')
except JSONDecodeError:
    print(f'\nРезультат:\n{response.text}\n')
