from deep_translator import GoogleTranslator
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QFontMetrics, QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

from config import Config


class TranslatorLogic:
    """Класс, управляющий логикой переводчика и взаимодействием с интерфейсом."""

    def __init__(self, ui: "TranslatorApp"):
        """Инициализирует логику переводчика."""
        self.ui = ui
        self.translation_history = []
        self.source_lang = "Русский"
        self.target_lang = "Алеутский"
        self.old_pos = None
        self.is_resizing = False
        self.resize_direction = 0
        self.resize_margin = 10

    @pyqtSlot()
    def translate_text(self) -> None:
        """Переводит текст из поля ввода и отображает результат в поле вывода."""
        try:
            input_text = self.ui.input_field.toPlainText().strip()
            # Соответствие языков кодам для GoogleTranslator
            lang_map = {"Русский": "ru", "Алеутский": "en"}
            source_lang = lang_map[self.source_lang]
            target_lang = lang_map[self.target_lang]

            if not input_text:
                self.ui.output_field.setText("Ошибка: Введите текст для перевода")
                return

            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(input_text)
            # Проверяем, если результат в байтах, декодируем в строку
            if isinstance(translated, bytes):
                translated = translated.decode("utf-8")
            # Отображаем переведённый текст или сообщение об ошибке
            self.ui.output_field.setText(
                translated if translated else "Ошибка: Не удалось перевести текст"
            )

            if translated:
                # Добавляем перевод в историю
                history_entry = {
                    "source_lang": self.source_lang,
                    "input_text": input_text,
                    "target_lang": self.target_lang,
                    "translated_text": translated,
                }
                self.translation_history.append(history_entry)
                # Ограничиваем историю 10 записями
                if len(self.translation_history) > 10:
                    self.translation_history.pop(0)
                self.update_history()

        except Exception as e:
            self.ui.output_field.setText(f"Ошибка перевода: {str(e)}")

    def swap_languages(self) -> None:
        """Меняет местами языки перевода и обновляет поля ввода/вывода."""
        # Меняем языки местами
        self.source_lang, self.target_lang = self.target_lang, self.source_lang
        # Обновляем метки языков
        self.ui.input_label.setText(self.source_lang)
        self.ui.output_label.setText(self.target_lang)
        # Меняем содержимое полей ввода и вывода
        input_text = self.ui.input_field.toPlainText().strip()
        output_text = self.ui.output_field.toPlainText().strip()
        if input_text or output_text:
            self.ui.input_field.setText(output_text)
            self.ui.output_field.setText(input_text)

    def on_input_text_changed(self) -> None:
        """Обрабатывает изменение текста в поле ввода."""
        self.ui.error_label.hide()
        self.ui.output_field.clear()
        if not self.ui.input_field.toPlainText().strip():
            self.ui.output_field.clear()

    def copy_output_text(self) -> None:
        """Копирует текст из поля вывода в буфер обмена."""
        text = self.ui.output_field.toPlainText().strip()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.ui.copy_tooltip.setText("Текст скопирован в буфер обмена")
        else:
            self.ui.copy_tooltip.setText("Поле вывода пустое, копировать нечего")

        # Показываем всплывающую подсказку
        self.ui.copy_tooltip.adjustSize()
        self.ui.copy_tooltip.show()
        self.ui.output_field.updateCopyContainerPosition()
        QTimer.singleShot(1000, self.hide_tooltip_and_reposition)

    def hide_tooltip_and_reposition(self) -> None:
        """Скрывает всплывающую подсказку и обновляет позицию контейнера копирования."""
        self.ui.copy_tooltip.hide()
        self.ui.output_field.updateCopyContainerPosition()

    def copy_symbol(self, symbol: str) -> None:
        """Копирует выбранный спецсимвол в буфер обмена."""
        clipboard = QApplication.clipboard()
        clipboard.setText(symbol)
        self.ui.symbols_popup.hide()

    def switch_section(self, section: str) -> None:
        """Переключает активную секцию приложения (переводчик, символы, о проекте)."""
        if section == "translator":
            self.ui.content_widget.show()
            if hasattr(self.ui, "about_widget"):
                self.ui.about_widget.hide()
            self.ui.menu_bar.translator_btn.setChecked(True)
            self.ui.menu_bar.symbols_btn.setChecked(False)
            self.ui.menu_bar.about_btn.setChecked(False)
        elif section == "symbols":
            if self.ui.symbols_popup.isVisible():
                self.ui.symbols_popup.hide()
            else:
                self.ui.symbols_popup.show_popup(self.ui.menu_bar.symbols_btn)
            self.ui.menu_bar.translator_btn.setChecked(False)
            self.ui.menu_bar.symbols_btn.setChecked(True)
            self.ui.menu_bar.about_btn.setChecked(False)
        elif section == "about":
            self.show_about_section()
            self.ui.menu_bar.translator_btn.setChecked(False)
            self.ui.menu_bar.symbols_btn.setChecked(False)
            self.ui.menu_bar.about_btn.setChecked(True)

    def show_about_section(self) -> None:
        """Показывает секцию 'О проекте'."""
        current_size = self.ui.size()
        was_maximized = self.ui.isMaximized()
        self.ui.setFixedSize(current_size)

        self.ui.setup_about_section()

        self.ui.setMinimumSize(*Config.MIN_SIZE)
        self.ui.setMaximumSize(16777, 16777)
        self.ui.resize(current_size)
        if was_maximized:
            self.ui.showMaximized()

    def update_history(self) -> None:
        """Обновляет отображение истории переводов."""
        # Очищаем текущую историю, кроме последнего элемента (spacer)
        while self.ui.history_layout.count() > 1:
            item = self.ui.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Добавляем карточки для каждой записи в истории
        for entry in self.translation_history:
            card = QWidget()
            card.setObjectName("historyCard")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(2)
            card_layout.setContentsMargins(10, 5, 10, 5)

            # Настраиваем шрифты для меток
            font = QFont("Arial", 14)
            font_bold = QFont("Arial", 14, QFont.Bold)
            font_metrics = QFontMetrics(font)

            # Метка для исходного языка
            source_lang_label = QLabel(entry["source_lang"])
            source_lang_label.setObjectName("historyLangLabel")
            source_lang_label.setFont(font_bold)
            source_lang_label.setFixedHeight(
                font_metrics.boundingRect(entry["source_lang"]).height()
            )
            source_lang_label.setFixedWidth(Config.HISTORY_CARD_WIDTH - 20)
            card_layout.addWidget(source_lang_label)

            # Метка для исходного текста
            source_text_label = QLabel(entry["input_text"])
            source_text_label.setObjectName("historyTextLabel")
            source_text_label.setFont(font)
            source_text_label.setWordWrap(False)
            source_text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            elided_text = font_metrics.elidedText(
                entry["input_text"], Qt.ElideRight, Config.HISTORY_CARD_WIDTH + 35
            )
            source_text_label.setText(elided_text)
            source_text_label.setFixedHeight(
                font_metrics.boundingRect(entry["input_text"]).height()
            )
            source_text_label.setFixedWidth(Config.HISTORY_CARD_WIDTH - 20)
            card_layout.addWidget(source_text_label)

            # Метка для целевого языка
            target_lang_label = QLabel(entry["target_lang"])
            target_lang_label.setObjectName("historyLangLabel")
            target_lang_label.setFont(font_bold)
            target_lang_label.setFixedHeight(
                font_metrics.boundingRect(entry["target_lang"]).height()
            )
            target_lang_label.setFixedWidth(Config.HISTORY_CARD_WIDTH - 20)
            card_layout.addWidget(target_lang_label)

            # Метка для переведённого текста
            target_text_label = QLabel(entry["translated_text"])
            target_text_label.setObjectName("historyTextLabel")
            target_text_label.setFont(font)
            target_text_label.setWordWrap(False)
            target_text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            elided_text = font_metrics.elidedText(
                entry["translated_text"], Qt.ElideRight, Config.HISTORY_CARD_WIDTH + 35
            )
            target_text_label.setText(elided_text)
            target_text_label.setFixedHeight(
                font_metrics.boundingRect(entry["translated_text"]).height()
            )
            target_text_label.setFixedWidth(Config.HISTORY_CARD_WIDTH - 20)
            card_layout.addWidget(target_text_label)

            # Устанавливаем фиксированный размер карточки
            card.setFixedHeight(Config.HISTORY_CARD_HEIGHT)
            card.setProperty("entry", entry)
            card.mousePressEvent = lambda event, c=card: self.on_card_clicked(c)
            self.ui.history_layout.insertWidget(0, card)

    def on_card_clicked(self, card: QWidget) -> None:
        """Обрабатывает клик по карточке истории, заполняя поля ввода и вывода."""
        entry = card.property("entry")
        if entry:
            self.ui.input_field.setText(entry["input_text"])
            self.ui.output_field.setText(entry["translated_text"])

    def clear_fields(self) -> None:
        """Очищает поля ввода и вывода."""
        self.ui.input_field.clear()
        self.ui.output_field.clear()

    def toggle_maximized(self) -> None:
        """Переключает состояние окна между развёрнутым и нормальным."""
        if self.ui.isMaximized():
            self.ui.showNormal()
            self.ui.maximize_button.setText("回")
        else:
            self.ui.showMaximized()
            self.ui.maximize_button.setText("❐")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает нажатие мыши для перемещения или изменения размера окна."""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            pos = event.pos()

            # Определяем, находится ли курсор на границе окна
            left = pos.x() <= self.resize_margin
            right = pos.x() >= self.ui.width() - self.resize_margin
            top = pos.y() <= self.resize_margin
            bottom = pos.y() >= self.ui.height() - self.resize_margin

            # Определяем направление изменения размера
            if left and top:
                self.resize_direction = 5  # Левый верхний угол
            elif right and top:
                self.resize_direction = 6  # Правый верхний угол
            elif left and bottom:
                self.resize_direction = 7  # Левый нижний угол
            elif right and bottom:
                self.resize_direction = 8  # Правый нижний угол
            elif left:
                self.resize_direction = 1  # Левая граница
            elif right:
                self.resize_direction = 2  # Правая граница
            elif top:
                self.resize_direction = 3  # Верхняя граница
            elif bottom:
                self.resize_direction = 4  # Нижняя граница
            else:
                self.resize_direction = 0  # Нет изменения размера

            self.is_resizing = self.resize_direction != 0

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает движение мыши для изменения курсора, перемещения или изменения размера окна."""
        pos = event.pos()
        # Определяем, находится ли курсор на границе окна
        left = pos.x() <= self.resize_margin
        right = pos.x() >= self.ui.width() - self.resize_margin
        top = pos.y() <= self.resize_margin
        bottom = pos.y() >= self.ui.height() - self.resize_margin

        # Устанавливаем форму курсора в зависимости от положения
        if (left and top) or (right and bottom):
            self.ui.setCursor(Qt.SizeFDiagCursor)
        elif (right and top) or (left and bottom):
            self.ui.setCursor(Qt.SizeBDiagCursor)
        elif left or right:
            self.ui.setCursor(Qt.SizeHorCursor)
        elif top or bottom:
            self.ui.setCursor(Qt.SizeVerCursor)
        else:
            self.ui.setCursor(Qt.ArrowCursor)

        if self.old_pos is not None:
            delta = event.globalPos() - self.old_pos
            min_width, min_height = Config.MIN_SIZE

            if self.is_resizing:
                # Изменяем размер окна в зависимости от направления
                x, y, w, h = self.ui.x(), self.ui.y(), self.ui.width(), self.ui.height()
                if self.resize_direction == 1:  # Левая граница
                    new_width = max(min_width, w - delta.x())
                    self.ui.setGeometry(x + delta.x(), y, new_width, h)
                elif self.resize_direction == 2:  # Правая граница
                    new_width = max(min_width, w + delta.x())
                    self.ui.resize(new_width, h)
                elif self.resize_direction == 3:  # Верхняя граница
                    new_height = max(min_height, h - delta.y())
                    self.ui.setGeometry(x, y + delta.y(), w, new_height)
                elif self.resize_direction == 4:  # Нижняя граница
                    new_height = max(min_height, h + delta.y())
                    self.ui.resize(w, new_height)
                elif self.resize_direction == 5:  # Левый верхний угол
                    new_width = max(min_width, w - delta.x())
                    new_height = max(min_height, h - delta.y())
                    self.ui.setGeometry(x + delta.x(), y + delta.y(), new_width, new_height)
                elif self.resize_direction == 6:  # Правый верхний угол
                    new_width = max(min_width, w + delta.x())
                    new_height = max(min_height, h - delta.y())
                    self.ui.setGeometry(x, y + delta.y(), w, new_height)
                elif self.resize_direction == 7:  # Левый нижний угол
                    new_width = max(min_width, w - delta.x())
                    new_height = max(min_height, h + delta.y())
                    self.ui.setGeometry(x + delta.x(), y, new_width, new_height)
                elif self.resize_direction == 8:  # Правый нижний угол
                    new_width = max(min_width, w + delta.x())
                    new_height = max(min_height, h + delta.y())
                    self.ui.resize(new_width, new_height)
            else:
                # Перемещаем окно, если не изменяем размер
                self.ui.move(self.ui.x() + delta.x(), self.ui.y() + delta.y())

            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает отпускание кнопки мыши, завершая перемещение или изменение размера."""
        self.old_pos = None
        self.is_resizing = False
        self.resize_direction = 0
        self.ui.setCursor(Qt.ArrowCursor)