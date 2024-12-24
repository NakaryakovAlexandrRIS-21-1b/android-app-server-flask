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