import sqlite3
from contextlib import contextmanager
import os
import regex as re
from datetime import datetime
import codecs

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.db_path = self.config.get('db_path')
        if self.is_initialized():
            self.ensure_tables_exist()

    def is_initialized(self):
        return bool(self.db_path) and os.path.exists(self.db_path)

    def initialize_database(self, path):
        print(f"Initializing database at {path}")
        self.db_path = path
        self.config.set('db_path', path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.ensure_tables_exist()
        print("Database initialization complete.")

    def ensure_tables_exist(self):
        """确保数据库表结构完整且最新"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取当前表结构
            cursor.execute("PRAGMA table_info(notes)")
            existing_columns = {column[1] for column in cursor.fetchall()}
            
            # 如果表不存在，创建新表
            if not existing_columns:
                cursor.execute('''
                    CREATE TABLE notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        imported BOOLEAN NOT NULL DEFAULT 0,
                        skipped BOOLEAN NOT NULL DEFAULT 0
                    )
                ''')
            else:
                # 检查并添加缺失的列
                required_columns = {
                    'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                    'content': 'TEXT NOT NULL',
                    'imported': 'BOOLEAN NOT NULL DEFAULT 0',
                    'skipped': 'BOOLEAN NOT NULL DEFAULT 0'
                }
                
                for col_name, col_type in required_columns.items():
                    if col_name not in existing_columns:
                        try:
                            cursor.execute(f'ALTER TABLE notes ADD COLUMN {col_name} {col_type}')
                        except Exception as e:
                            # 主键列无法通过 ALTER TABLE 添加，需要特殊处理
                            if 'PRIMARY KEY' not in str(e):
                                raise e
            
            conn.commit()

    @contextmanager
    def get_connection(self):
        if not self.db_path:
            raise ValueError("数据库路径未设置")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def add_notes(self, notes):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("INSERT INTO notes (content, imported) VALUES (?, ?)",
                               [(note['content'], note.get('imported', False)) for note in notes])
            conn.commit()

    def update_note(self, note):
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE notes
                SET content = ?, imported = ?
                WHERE id = ?
            ''', (note['content'], note.get('imported', False), note['id']))
            conn.commit()
        print(f"Note {note['id']} updated in database")

    def update_note_content(self, note_id, content):
        """仅更新笔记的内容"""
        with self.get_connection() as conn:
            conn.execute('UPDATE notes SET content = ? WHERE id = ?', (content, note_id))
            conn.commit()
        print(f"Note {note_id} content updated in database")

    def get_notes(self, imported=False):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, content FROM notes WHERE imported = ?", (imported,))
                return [{'id': row[0], 'content': row[1]} for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            print(f"数据库操作错误: {e}")
            return []

    def clear_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes")
            conn.commit()

    def rename_database(self, new_path):
        os.rename(self.db_path, new_path)
        self.db_path = new_path
        self.config.set('db_path', new_path)

    def delete_note(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()

    def get_note(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, imported FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            if row:
                return {'id': row[0], 'content': row[1], 'imported': bool(row[2])}
            return None

    def get_notes_summary(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否存在 skipped 列
            cursor.execute("PRAGMA table_info(notes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'skipped' in columns:
                cursor.execute("SELECT id, content, imported, skipped FROM notes")
            else:
                # 如果没有 skipped 列，使用默认值
                cursor.execute("SELECT id, content, imported, 0 as skipped FROM notes")
                
            return [dict(row) for row in cursor.fetchall()]

    def add_note(self, content, imported=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (content, imported) VALUES (?, ?)",
                           (content, imported))
            conn.commit()

    def mark_note_as_imported(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE notes SET imported = ? WHERE id = ?", (True, note_id))
            conn.commit()

    def mark_note_as_skipped(self, note_id):
        """将笔记标记为已跳过"""
        try:
            # 确保表结构正确
            self.ensure_tables_exist()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 更新状态
                cursor.execute("UPDATE notes SET skipped = ? WHERE id = ?", (True, note_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"标记笔记为已跳过时出错: {str(e)}")
            return False

    def find_and_replace(self, find_pattern, replace_text, use_regex=False):
        """查找替换，使用 regex 库并提供稳健的输入处理"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM notes")
            notes = cursor.fetchall()
            modified_count = 0
            
            processed_replace_text = replace_text
            if use_regex:
                # 稳健的转义处理流程，在应用层闭环
                # 1. 用户想要输入真实的 \n (换行) 或 \t (制表符), 他们会输入 \\n 或 \\t
                #    我们先把这些明确的转义序列转换为真实的字符
                processed_replace_text = processed_replace_text.replace('\\\\', '\\').replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                
                # 2. 然后，我们将用户输入的、用于捕获组的 $1 或 \1 统一转换为引擎能识别的 \1 格式
                #    使用一个不会被用户轻易输入的临时标记来避免冲突
                processed_replace_text = re.sub(r'\\(\d+)', r'__TEMP_BACKSLASH_GROUP_\1__', processed_replace_text)
                processed_replace_text = re.sub(r'\$(\d+)', r'\\\1', processed_replace_text)
                processed_replace_text = re.sub(r'__TEMP_BACKSLASH_GROUP_(\d+)__', r'\\\1', processed_replace_text)

            for note_id, content in notes:
                if use_regex:
                    try:
                        new_content = re.sub(find_pattern, processed_replace_text, content)
                    except re.error:
                        continue
                else:
                    new_content = content.replace(find_pattern, replace_text)
                    
                if new_content != content:
                    cursor.execute("UPDATE notes SET content = ? WHERE id = ?", 
                                 (new_content, note_id))
                    modified_count += 1
            
            conn.commit()
            return modified_count

    def restore_skipped_note(self, note_id):
        """将已跳过的笔记恢复到未导入状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 更新状态：取消跳过标记
                cursor.execute("""
                    UPDATE notes 
                    SET skipped = ?, imported = ? 
                    WHERE id = ?
                """, (False, False, note_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"恢复已跳过笔记时出错: {str(e)}")
            return False

    def create_database_copy(self):
        """创建数据库副本，替换已有时间戳"""
        if not self.db_path:
            raise ValueError("数据库路径未设置")
            
        # 解析当前文件名
        dir_path = os.path.dirname(self.db_path)
        current_name = os.path.splitext(os.path.basename(self.db_path))[0]
        
        # 移除已有的时间戳格式（如果存在）
        # 匹配格式：基础名称-YYYY-MM-DD-HHMMSS
        base_name = re.sub(r'-\d{4}-\d{2}-\d{2}-\d{6}$', '', current_name)
        
        # 生成新的时间戳文件名
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        new_filename = f"{base_name}-{timestamp}.db"
        new_path = os.path.join(dir_path, new_filename)
        
        try:
            # 确保数据库连接已关闭
            self._connection = None
            
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, new_path)
            
            # 更新数据库路径并重新连接
            self.db_path = new_path
            self.ensure_tables_exist()
            
            return new_path
        except Exception as e:
            # 如果出错，尝试恢复原来的连接
            self.db_path = self.db_path
            self.ensure_tables_exist()
            raise Exception(f"创建数据库副本失败: {str(e)}")

    def remove_empty_lines(self):
        """使用正则表达式删除所有笔记中的空行"""
        try:
            # 匹配一个或多个空行（包括只包含空白字符的行）
            empty_line_pattern = r'(?:\r?\n|\r)[ \t]*(?:\r?\n|\r)+'
            # 替换为单个换行符
            return self.find_and_replace(empty_line_pattern, '\n', use_regex=True)
        except Exception as e:
            print(f"删除空行时出错: {str(e)}")
            raise e
