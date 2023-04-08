from flask import Flask, jsonify, request, send_file, render_template
from collections import deque
import time
import os
import psutil
import requests
import socket

app = Flask(__name__)

if not os.path.exists('files'):
        os.makedirs('files')

# Создаем список нод для пинга
nodes = ['NODE', 'NODE']

# Создаем переменные-блокираторы и пароль
lock_get_file = False
lock_load_file = True
lock_status = False

password = r'YOURPASSHERE'

# Создаем словарь для хранения очередей запросов от каждого IP
ip_queue = {}

# Максимальное количество запросов от одного IP за заданный интервал времени
max_requests = 30

# Интервал времени, в течение которого мы ограничиваем количество запросов
interval = 60

# Функция для проверки количества запросов от IP-адреса
def is_allowed(ip):
        if ip not in ip_queue:
                # Если IP встречается впервые, создаем для него новую очередь запросов
                ip_queue[ip] = deque([time.time()], maxlen=max_requests)
        else:
                # Добавляем текущий запрос в очередь и проверяем количество запросов за последний интервал времени
                ip_queue[ip].append(time.time())
                if len(ip_queue[ip]) == max_requests and ip_queue[ip][-1] - ip_queue[ip][0] < interval:
                        # Если количество запросов превышает порог и время между первым и последним запросом меньше интервала, блокируем доступ
                        return False
        return True

# Middleware-функция для проверки количества запросов от IP-адреса
@app.before_request
def limit_requests():
        if not is_allowed(request.remote_addr):
                return jsonify({'error': 'Too many requests'}), 429, {'Content-Type': 'application/json'}
        

@app.route('/', methods=['HEAD'])
def head():
        return jsonify({'message': 'Hello, world'}), 200, {'Content-Type': 'application/json'}


@app.route('/', methods=['GET'])
def index():
        return render_template('index.html'), 200, {'Content-Type': 'text/html'}


@app.route('/favicon.ico')
def favicon():
        return app.send_static_file('favicon.ico')


@app.route("/<filename>")
def get_file(filename):
        """
        It opens a file and returns the file object.

        :param filename: The name of the file you want to download
        """
        if lock_get_file and request.args.get('key') != password:
                return jsonify({'error': 'Access denied'}), 403, {'Content-Type': 'application/json'}
        if os.path.isfile(os.path.join('files', filename)):
                # Если файл найден на главном сервере, возвращаем его
                return (
                        open(os.path.join('files', filename), 'r').read(),
                        200,
                        {'Content-Type': 'application/json'},
                )
        # Если файл не найден на главном сервере, ищем его на всех узлах
        for node in nodes:
                try:
                        # Отправляем запрос на проверку наличия файла на узле
                        response = requests.get(f"{node}/{filename}", params={'key': password})
                        if response.status_code == 200:
                                # Если файл найден на узле, возвращаем его
                                return response.content, 200, {'Content-Type': 'application/json'}
                except:
                        # Если узел недоступен, переходим к следующему
                        continue
        # Если файл не найден на главном сервере и на узлах, возвращаем ошибку
        return (
                jsonify({'error': 'File not found'}),
                404,
                {'Content-Type': 'application/json'},
        )


@app.route("/load", methods=["POST"])
def load_file():
    """
        It uploads a file to a server
        """
    if request.args.get('filename'):
        # Получаем имя файла без расширения из аргументов запроса
        filename_without_extension = request.args.get('filename')
    else:
         return jsonify({'error': 'Invalid filename'}), 400, {'Content-Type': 'application/json'}

    if lock_load_file and request.args.get('key') != password:
        return jsonify({'error': 'Access denied'}), 403, {
            'Content-Type': 'application/json'
        }
    # Получаем файл из POST запроса
    file = request.files.get("file")

    # Проверяем, что файл получен и имеет допустимое расширение
    if not file or not file.filename.endswith(('.txt')):
        return jsonify({'error': 'Invalid file'}), 400, {
            'Content-Type': 'application/json'
        }

    # Формируем имя файла с расширением
    filename = f"{filename_without_extension}.txt"

    if os.path.isfile(os.path.join('files', filename)):
         os.remove(os.path.join('files', filename))

    # Получаем информацию о свободном месте на диске в килобайтах на главном сервере
    free_space = psutil.disk_usage('/').free // 1024
    # Получаем размер файла, который будет сохранен на диск в килобайтах
    file_size = len(file.read()) // 1024

    # Получаем hostname сервера
    hostname = socket.gethostname()
    # Получаем IP-адрес сервера
    ip_address = socket.gethostbyname(hostname)

    # Формируем ссылку на сервер
    server_url = f"http://{ip_address}"
    if request.host:
        server_url = f"{request.scheme}://{request.host}"

    # Проверяем, что на главном сервере достаточно свободного места для сохранения файла
    if file_size >= free_space:
        for node in nodes:
            try:
                free = requests.get(f'{node}/status', params={
                    'key': password
                }).json()['free_space']
            except:
                continue
            if free > file_size:
                # Если на ноде есть свободное место, загружаем файл на диск
                response = requests.post(f'{node}/load',
                                                                 files={'file': file},
                                                                 params={'key': password, 'filename': filename_without_extension})
                if response.status_code == 200:
                    # Если файл успешно сохранен на резервном сервере, возвращаем ссылку на него
                    return jsonify({'file_link':
                                                    f'{node}/{filename}'}), 200, {
                                                        'Content-Type': 'application/json'
                                                    }
                else:
                    # Если произошла ошибка при сохранении файла на резервном сервере, возвращаем ошибку
                    continue
    else:
        # Если на главном сервере достаточно места, сохраняем файл на нем
        file.seek(0)    # сбрасываем указатель на начало файла
        file.save(os.path.join(os.getcwd(), 'files', filename))

        # Возвращаем ссылку на загруженный файл в JSON формате
        return jsonify({'file_link':
                                        f'{server_url}/{filename}'}), 200, {
                                            'Content-Type': 'application/json'
                                        }




@app.route('/status', methods=["GET"])
def status():
        if lock_status and request.args.get('key') != password:
                return jsonify({'error': 'Access denied'}), 403, {'Content-Type': 'application/json'}
        # Получаем информацию о диске
        usage = psutil.disk_usage("/")
        # Вычисляем свободное место в байтах
        free_space = int(usage.free / 1024)
        # Возвращаем JSON-ответ с информацией о свободном месте на сервере
        return jsonify({'free_space': free_space})

@app.route('/config', methods=["GET"])
def config():
        return jsonify({'lock_get_file': lock_get_file, 'lock_load_file': lock_load_file, 'lock_status': lock_status})

if __name__ == "__main__":
        app.run(host='0.0.0.0', port=80)
