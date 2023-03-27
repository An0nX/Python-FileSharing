from flask import Flask, jsonify, request, send_file, render_template
from collections import deque
import time
import os
import psutil

app = Flask(__name__)

if not os.path.exists('files'):
    os.makedirs('files')

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
    return (
        (
            open(os.path.join('files', filename), 'r').read(),
            200,
            {'Content-Type': 'application/json'},
        )
        if os.path.isfile(os.path.join('files', filename))
        else (
            jsonify({'error': 'File not found'}),
            404,
            {'Content-Type': 'application/json'},
        )
    )


@app.route("/download/<filename>")
def download_file(filename):
    """
    It downloads a file from the server.
    
    :param filename: The name of the file you want to download
    """
    # Проверяем, что запрашиваемый файл существует
    if not os.path.isfile(os.path.join(os.getcwd(), 'files', filename)):
        return jsonify({'error': 'File not found'}), 404, {'Content-Type': 'application/json'}

    # Проверяем, что запрашиваемый файл соответствует требуемому файлу
    if filename != os.path.basename(filename):
        return jsonify({'error': 'File not found'}), 404, {'Content-Type': 'application/json'}

    # Если файл существует, выдаем его на скачивание в JSON формате
    return send_file(os.path.join(os.getcwd(), 'files', filename), as_attachment=True), 200, {'Content-Type': 'application/json'}


@app.route("/load", methods=["POST"])
def load_file():
    """
    It uploads a file to a server
    """
    # Получаем файл из POST запроса
    file = request.files.get("file")

    # Проверяем, что файл получен и имеет допустимое расширение
    if not file or not file.filename.endswith(('.txt')):
        return jsonify({'error': 'Invalid file'}), 400, {'Content-Type': 'application/json'}

    # Получаем имя файла с расширением
    filename = file.filename

    # Получаем информацию о свободном месте на диске в килобайтах
    free_space = psutil.disk_usage('/').free // 1024
    # Получаем размер файла, который будет сохранен на диск в килобайтах
    file_size = len(file.read()) // 1024

    # Проверяем, что на диске достаточно свободного места для сохранения файла
    if file_size >= free_space:
        return jsonify({'error': 'Not enough free space on disk'}), 400, {'Content-Type': 'application/json'}

    # Сохраняем файл по пути, указывая имя файла
    file.seek(0) # сбрасываем указатель на начало файла
    file.save(os.path.join(os.getcwd(), 'files', filename))

    # Возвращаем ссылку на загруженный файл в JSON формате
    return jsonify({'file_link': f'/download/{os.path.basename(filename)}'}), 200, {'Content-Type': 'application/json'}



@app.route('/status', methods=["GET"])
def status():
    # Получаем информацию о диске
    usage = psutil.disk_usage("/")
    # Вычисляем свободное место в байтах
    free_space = int(usage.free / 1024)
    # Возвращаем JSON-ответ с информацией о свободном месте на сервере
    return jsonify({'free_space': free_space})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)