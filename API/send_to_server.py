import requests

url = input("Ссылка для загрузки: ")

response = requests.get(f'{url}/config').json()

# Путь к файлу, который нужно отправить на сервер
file_path = r"".join(input("Введите путь к файлу: "))

# Открываем файл и отправляем его на сервер
try:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        if response['lock_load_file']:
            response = requests.post(f'{url}/load', files=files, params={'key': input('Введите пароль: ')}).json()
        else:
            response = requests.post(f'{url}/load', files=files).json()
except FileNotFoundError:
    print(f"Файл {file_path} не найден")

if not response['error']:
    # Печатаем ссылку на загруженный файл
    print(f"Результат:\n{response['file_link']}\n")
else:
    print(f"Ошибка: {response['error']}\n")
