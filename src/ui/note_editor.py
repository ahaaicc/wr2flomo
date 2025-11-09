from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

class NoteEditorWidget(QWidget):
    # 信号：当笔记内容在本地编辑器中发生变化时发出
    # 不再直接关联数据库保存
    note_changed_locally = pyqtSignal(dict)
    
    # 信号：当用户明确点击“保存”时发出
    save_triggered = pyqtSignal(dict)

    def __init__(self, note, parent=None):
        super().__init__(parent, Qt.WindowType.Tool)
        self.note = note
        self.init_ui()
        # 移除自动保存定时器
        # self.setup_auto_save()
        self.note_edit.textChanged.connect(self.on_text_changed)

    def init_ui(self):
        self.setWindowTitle("编辑笔记")
        layout = QVBoxLayout()

        self.note_edit = QPlainTextEdit()
        self.note_edit.setPlainText(self.note.get('content', ''))
        layout.addWidget(self.note_edit)

        save_btn = QPushButton("保存 (Ctrl+S)")
        save_btn.clicked.connect(self.trigger_save)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        QShortcut(QKeySequence("Ctrl+S"), self, self.trigger_save)

    def on_text_changed(self):
        """当文本编辑器内容改变时，发出本地变更信号"""
        self.note['content'] = self.note_edit.toPlainText()
        self.note_changed_locally.emit(self.note)

    def trigger_save(self):
        """用户点击保存按钮或使用快捷键时，发出保存触发信号"""
        self.note['content'] = self.note_edit.toPlainText()
        self.save_triggered.emit(self.note)

    # 移除定时器和相关逻辑
    # def setup_auto_save(self):
    #     self.auto_save_timer = QTimer(self)
    #     self.auto_save_timer.timeout.connect(self.save_note)
    #     self.auto_save_timer.start(60000)

    def set_note(self, note):
        self.note = note
        self.note_edit.setPlainText(note.get('content', ''))
        self.setWindowTitle(f"编辑笔记 - ID: {note.get('id', '新笔记')}")

    def closeEvent(self, event):
        # 关闭窗口时不再自动保存
        # self.save_note()
        super().closeEvent(event)
