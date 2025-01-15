from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QLineEdit, 
                           QPushButton, QLabel, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
import re

class NoteSplitterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 笔记输入区
        self.note_input = QTextEdit()
        layout.addWidget(QLabel("请粘贴读书笔记:"))
        layout.addWidget(self.note_input)
        
        # 分隔符输入
        self.separator_input = QLineEdit()
        layout.addWidget(QLabel("分隔标识符(支持正则表达式):"))
        layout.addWidget(self.separator_input)
        
        # 正则表达式开关
        self.use_regex = QCheckBox("使用正则表达式")
        self.use_regex.setChecked(True)
        layout.addWidget(self.use_regex)
        
        # 预览按钮
        preview_btn = QPushButton("预览分割结果")
        preview_btn.clicked.connect(self.preview_split)
        layout.addWidget(preview_btn)
        
        # 分割按钮
        split_btn = QPushButton("确认拆分")
        split_btn.clicked.connect(self.split_notes)
        layout.addWidget(split_btn)
        
        # 预览区域
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setPlaceholderText("分割预览将显示在这里...")
        layout.addWidget(QLabel("预览结果:"))
        layout.addWidget(self.preview_area)
        
        self.setLayout(layout)
        self.setWindowTitle("笔记拆分")
        self.resize(600, 800)

    def split_content(self):
        content = self.note_input.toPlainText()
        separator = self.separator_input.text().strip()
        
        if not separator or not content:
            raise ValueError("请输入分隔标识符和笔记内容")

        if self.use_regex.isChecked():
            try:
                # 使用正则表达式进行分割，但保留分隔符
                pattern = re.compile(f'({separator})', re.MULTILINE)
                # 分割后重新组合，确保分隔符保留在每条笔记的开头
                parts = pattern.split(content)
                split_notes = []
                current_note = []
                
                for part in parts:
                    if pattern.match(part):  # 是分隔符
                        if current_note:  # 如果已有内容，保存为一条笔记
                            split_notes.append(''.join(current_note))
                        current_note = [part]  # 开始新的笔记，保留分隔符
                    else:
                        current_note.append(part)
                
                if current_note:  # 添加最后一条笔记
                    split_notes.append(''.join(current_note))
                
                # 过滤空白内容
                split_notes = [note.strip() for note in split_notes if note.strip()]
                
            except re.error as e:
                raise ValueError(f"正则表达式错误: {str(e)}")
        else:
            # 普通字符串分割
            lines = content.split('\n')
            split_notes = []
            current_note = []
            
            for line in lines:
                if separator in line:
                    if current_note:
                        split_notes.append('\n'.join(current_note))
                        current_note = []
                current_note.append(line)
            
            if current_note:
                split_notes.append('\n'.join(current_note))

        return split_notes

    def preview_split(self):
        """预览分割结果"""
        try:
            split_notes = self.split_content()
            
            if not split_notes:
                self.preview_area.setPlainText("没有找到可分割的内容")
                return
                
            preview_text = "\n\n=== 分割线 ===\n\n".join(
                f"笔记 {i+1}:\n{note}" 
                for i, note in enumerate(split_notes)
            )
            
            self.preview_area.setPlainText(preview_text)
            
        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}")

    def split_notes(self):
        """确认分割并返回结果"""
        try:
            split_notes = self.split_content()
            
            if not split_notes:
                QMessageBox.warning(self, "警告", "没有找到可分割的内容")
                return
                
            self.split_notes = split_notes
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分割失败: {str(e)}")

    def get_split_notes(self):
        return self.split_notes
