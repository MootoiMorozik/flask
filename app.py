import os
import subprocess
from flask import Flask, request, render_template, send_from_directory, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Главная страница ---
@app.route("/")
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("index.html", files=files)

# --- Загрузка файлов ---
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "Нет файла", 400
    f = request.files["file"]
    if f.filename == "":
        return "Пустое имя файла", 400
    path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(path)
    return "Файл загружен"

# --- Скачивание файлов ---
@app.route("/uploads/<path:filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# --- Выполнение произвольной команды ---
@app.route("/exec", methods=["POST"])
def exec_cmd():
    cmd = request.json.get("cmd")
    if not cmd:
        return jsonify({"error": "нет команды"}), 400
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            text=True,
            executable="/bin/bash"
        )
        return jsonify({"output": output})
    except subprocess.CalledProcessError as e:
        return jsonify({"output": e.output, "code": e.returncode})

# --- Запуск команд из Procfile (выполняется в uploads/) ---
@app.route("/procfile/run", methods=["POST"])
def run_procfile():
    procfile_path = "Procfile"
    if not os.path.exists(procfile_path):
        return jsonify({"error": "Procfile не найден"}), 404

    results = {}
    with open(procfile_path) as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            name, cmd = line.split(":", 1)
            try:
                out = subprocess.check_output(
                    cmd.strip(),
                    shell=True,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=UPLOAD_FOLDER,
                    executable="/bin/bash"
                )
                results[name.strip()] = out
            except subprocess.CalledProcessError as e:
                results[name.strip()] = f"Ошибка {e.returncode}: {e.output}"

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)