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
