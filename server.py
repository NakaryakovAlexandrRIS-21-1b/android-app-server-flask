from flask import Flask, request, jsonify
from threading import Timer, Lock
import logging
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Note:
    def __init__(self, note_id, deadline, text=""):
        self.note_id = note_id
        self.deadline = deadline
        self.text = text
        self.timer = None
        
    def schedule(self):
        delay = (self.deadline - datetime.now()).total_seconds()
        if delay > 0:
            self.timer = Timer(delay, self.trigger)
            self.timer.start()
            logger.info(f"Заметка создана: ID={self.note_id}, Дедлайн={self.deadline}, Текст={self.text}")
        else:
            logger.warning(f"Заметка {self.note_id} имеет прошедший дедлайн.")

    def cancel(self):
        if self.timer:
            self.timer.cancel()
            logger.info(f"Заметка отменена: ID={self.note_id}")
            
    def trigger(self):
        logger.info(f"Заметка сработала! ID={self.note_id}, Текст={self.text}")
        with notes_lock:
            notes.pop(self.note_id, None)
        logger.info(f"Заметка удалена: ID={self.note_id}")
        
def validate_request_data(data):
    if not data:
        return jsonify({"error": "Пустой запрос."}), 400

    if len(str(data)) > 1000:
        return jsonify({"error": "Размер запроса превышает допустимый предел (1000 символов)."}), 400

    try:
        note_id = int(data.get('id'))
        deadline_hours = int(data.get('hours'))
        deadline_minutes = int(data.get('minutes'))
        text = data.get('text', "")
    except (TypeError, ValueError):
        return jsonify({"error": "Некорректный формат данных. Проверьте 'id', 'hours' и 'minutes'."}), 400

    return note_id, deadline_hours, deadline_minutes, text

@app.route('/create_note', methods=['POST'])
def create_note():
    try:
        #force=True: Позволяет парсить данные даже если Content-Type не установлен как application/json.
        #silent=True: Не выбрасывает исключение, если JSON некорректный, вместо этого возвращает None.
        data = request.get_json(force=True, silent=True)

        if data is None:
            return jsonify({"error": "Тело запроса должно быть корректным JSON."}), 400
        
        if not isinstance(data, dict):
            return jsonify({"error": "JSON должен быть объектом (словарем)."}), 400

        # Проверка данных
        validate_response = validate_request_data(data)
        if isinstance(validate_response, tuple) and len(validate_response) == 4:
            note_id, deadline_hours, deadline_minutes, text = validate_response
        else:
            # Если возвращается ошибка из validate_request_data
            return validate_response

        note_id, deadline_hours, deadline_minutes, text = validate_response

        deadline = datetime.now().replace(hour=deadline_hours, minute=deadline_minutes, second=0, microsecond=0)
        if deadline < datetime.now():
            deadline += timedelta(days=1)

        with notes_lock:
            for existing_note in notes.values():
                if existing_note.deadline == deadline:
                    return jsonify({"error": "Заметка на это время уже существует."}), 400

            if note_id in notes:
                return jsonify({"error": f"Заметка с ID {note_id} уже существует."}), 400

            new_note = Note(note_id, deadline, text)
            notes[note_id] = new_note
            new_note.schedule()

        return jsonify({"message": f"Заметка {note_id} создана."}), 201
    
    except Exception as e:
        # Обработка непредвиденных исключений
        return jsonify({"error": "Ошибка обработки запроса.", "details": str(e)}), 500


@app.route('/delete_note/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    # Проверка, что note_id - число (дополнительная защита)
    if not note_id.isdigit():
        return jsonify({"error": "ID заметки должен быть числом."}), 400
    
    note_id = int(note_id)

    # Проверка на корректность диапазона ID

if note_id < 0:
        return jsonify({"error": "ID заметки не может быть отрицательным."}), 400

    with notes_lock:
        note = notes.pop(note_id, None)
        if note:
            note.cancel()
            return jsonify({"message": f"Заметка {note_id} отменена."}), 200
        else:
            return jsonify({"error": f"Заметка {note_id} не найдена."}), 404


@app.route('/get_notes', methods=['GET'])
def get_notes():
    try:
        with notes_lock:
            active_note_ids = list(notes.keys())
        return jsonify({"notes": active_note_ids}), 200

    except Exception as e:
        return jsonify({"error": "Ошибка при получении заметок.", "details": str(e)}), 500


@app.route('/update_note', methods=['PUT'])
def update_note():
    try:
        #force=True: Позволяет парсить данные даже если Content-Type не установлен как application/json.
        #silent=True: Не выбрасывает исключение, если JSON некорректный, вместо этого возвращает None.
        data = request.get_json(force=True, silent=True)

        if data is None:
            return jsonify({"error": "Тело запроса должно быть корректным JSON."}), 400
        
        if not isinstance(data, dict):
            return jsonify({"error": "JSON должен быть объектом (словарем)."}), 400
        
        # Проверка данных
        validate_response = validate_request_data(data)
        if isinstance(validate_response, tuple) and len(validate_response) == 4:
            note_id, deadline_hours, deadline_minutes, text = validate_response
        else:
            # Если возвращается ошибка из validate_request_data
            return validate_response

        note_id, deadline_hours, deadline_minutes, text = validate_response

        deadline = datetime.now().replace(hour=deadline_hours, minute=deadline_minutes, second=0, microsecond=0)
        if deadline < datetime.now():
            deadline += timedelta(days=1)

        with notes_lock:
            note = notes.get(note_id)
            if note:
                note.cancel()

            updated_note = Note(note_id, deadline, text)
            notes[note_id] = updated_note
            updated_note.schedule()

        logger.info(f"Заметка обновлена: ID={note_id}, Новое время={deadline}, Новый текст={text}")
        return jsonify({"message": f"Заметка {note_id} обновлена."}), 200
    
    except Exception as e:
        # Обработка непредвиденных исключений
        return jsonify({"error": "Ошибка обработки запроса.", "details": str(e)}), 500

