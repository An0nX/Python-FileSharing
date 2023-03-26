from flask import Flask, abort, jsonify, request, send_file
import os

app = Flask(__name__)

if not os.path.exists('files'):
    os.makedirs('files')

@app.route("/<filename>")
def get_file(filename):
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
    # Получаем файл из POST запроса
    file = request.files.get("file")

    # Проверяем, что файл получен и имеет допустимое расширение
    if not file or not file.filename.endswith(('.txt')):
        return jsonify({'error': 'Invalid file'}), 400, {'Content-Type': 'application/json'}

    # Получаем имя файла с расширением
    filename = file.filename

    # Сохраняем файл по пути, указывая имя файла
    file.save(os.path.join(os.getcwd(), 'files', filename))

    # Возвращаем ссылку на загруженный файл в JSON формате
    return jsonify({'file_link': f'/download/{os.path.basename(filename)}'}), 200, {'Content-Type': 'application/json'}


if __name__ == "__main__":
    app.run()
