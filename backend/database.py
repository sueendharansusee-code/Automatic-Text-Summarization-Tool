import os
import sqlite3
from datetime import datetime

# Default database path inside the project's data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'summaries.db')


def get_db_connection(db_path=DB_PATH):
    """
    Creates and returns a connection to the SQLite database.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    """
    Initializes the database schema if tables do not exist.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            length_setting TEXT NOT NULL DEFAULT 'medium',
            original_word_count INTEGER NOT NULL,
            summary_word_count INTEGER NOT NULL,
            compression_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_summary(original_text, summary_text, length_setting, original_word_count, summary_word_count, compression_rate, db_path=DB_PATH):
    """
    Saves a generated summary record into SQLite database.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO summaries (
            original_text, summary_text, length_setting,
            original_word_count, summary_word_count, compression_rate, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        original_text,
        summary_text,
        length_setting,
        original_word_count,
        summary_word_count,
        compression_rate,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    summary_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return summary_id


def get_all_summaries(limit=50, db_path=DB_PATH):
    """
    Retrieves history of generated summaries, ordered by created_at descending.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_text, summary_text, length_setting,
               original_word_count, summary_word_count, compression_rate, created_at
        FROM summaries
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            'id': row['id'],
            'original_text': row['original_text'],
            'summary_text': row['summary_text'],
            'length_setting': row['length_setting'],
            'original_word_count': row['original_word_count'],
            'summary_word_count': row['summary_word_count'],
            'compression_rate': row['compression_rate'],
            'created_at': row['created_at']
        })
    return result


def get_summary_by_id(summary_id, db_path=DB_PATH):
    """
    Retrieves a single summary record by ID.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_text, summary_text, length_setting,
               original_word_count, summary_word_count, compression_rate, created_at
        FROM summaries
        WHERE id = ?
    ''', (summary_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row['id'],
            'original_text': row['original_text'],
            'summary_text': row['summary_text'],
            'length_setting': row['length_setting'],
            'original_word_count': row['original_word_count'],
            'summary_word_count': row['summary_word_count'],
            'compression_rate': row['compression_rate'],
            'created_at': row['created_at']
        }
    return None


def delete_summary(summary_id, db_path=DB_PATH):
    """
    Deletes a single summary record from history.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM summaries WHERE id = ?', (summary_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def clear_all_summaries(db_path=DB_PATH):
    """
    Deletes all summary records from history.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM summaries')
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected
