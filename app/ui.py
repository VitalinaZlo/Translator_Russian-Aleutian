import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QGridLayout, QScrollArea, QFrame)

from PyQt5.QtGui import QPixmap, QPalette, QBrush, QPainter, QIcon, QMouseEvent, QResizeEvent
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QPoint, QEvent

from logic import TranslatorLogic
from config import Config


class OutputTextEdit(QTextEdit):
    """Класс для текстового поля вывода с поддержкой контейнера копирования."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.copy_container = None
        self.updateViewportMargins()

    def setCopyContainer(self, container: QWidget) -> None:
        """Устанавливает контейнер для кнопки копирования."""
        self.copy_container = container

    def updateViewportMargins(self) -> None:
        """Динамически обновляет viewportMargins в зависимости от размера."""
        if self.copy_container:
            right_margin = max(30, self.copy_container.width() + 10)
            bottom_margin = max(30, self.copy_container.height() + 10)

            # Если поле слишком маленькое, уменьшаем отступы
            if self.width() < 200:
                right_margin = 10
            if self.height() < 150:
                bottom_margin = 10
            self.setViewportMargins(0, 0, right_margin, bottom_margin)
        else:
            self.setViewportMargins(0, 0, 0, 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Обновляет позицию контейнера копирования при изменении размера."""
        super().resizeEvent(event)
        if self.copy_container:
            self.updateCopyContainerPosition()

    def updateCopyContainerPosition(self) -> None:
        """Обновляет позицию контейнера копирования в правом нижнем углу."""
        if self.copy_container:
            self.copy_container.adjustSize()
            x = self.width() - self.copy_container.width() - 10
            y = self.height() - self.copy_container.height() - 10
            self.copy_container.move(x, y)
            self.copy_container.raise_()

            # Скрываем контейнер, если поле вывода слишком маленькое
            if self.width() < 300 or self.height() < 50:
                self.copy_container.hide()
            else:
                self.copy_container.show()
                self.copy_container.move(x, y)
                self.copy_container.raise_()


class SymbolsPopup(QWidget):
    """Класс для всплывающего окна со специальными символами."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Инициализирует интерфейс всплывающего окна."""
        self.setWindowFlags(Qt.Popup | Qt.NoDropShadowWindowHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("symbolsPopup")

        # Контейнер для символов
        self.container = QWidget(self)
        self.container.setObjectName("symbolsContainer")
        self.container.setAttribute(Qt.WA_TranslucentBackground, False)

        # Горизонтальный layout для кнопок символов
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(15)

        # Добавляем кнопки для символов
        symbols = ["x̂", "ĝ", "ẍ"]
        for symbol in symbols:
            self.add_symbol_button(symbol)

        # Основной layout для всплывающего окна
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def add_symbol_button(self, symbol: str) -> None:
        """Добавляет кнопку для указанного символа."""
        btn = QPushButton(symbol, self.container)
        btn.setObjectName("symbolButton")
        btn.setFixedSize(Config.SYMBOL_BUTTON_SIZE)
        btn.clicked.connect(lambda: self.parent().logic.copy_symbol(symbol))
        self.layout.addWidget(btn)

    def show_popup(self, parent_button: QPushButton) -> None:
        """Показывает всплывающее окно под указанной кнопкой."""
        self.adjustSize()
        vertical_offset = 10
        pos = parent_button.mapToGlobal(QPoint(0, parent_button.height() + vertical_offset))
        x_pos = pos.x() - (self.width() - parent_button.width()) // 2
        self.move(x_pos, pos.y())
        self.show()


class MenuBar(QWidget):
    """Класс для панели меню с переключением секций."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("menuBar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 5, 20, 5)
        self.layout.setSpacing(20)

        # Кнопки меню
        self.translator_btn = QPushButton("Переводчик")
        self.symbols_btn = QPushButton("Спецсимволы")
        self.about_btn = QPushButton("О проекте")

        # Настройка кнопок меню
        for btn in [self.translator_btn, self.symbols_btn, self.about_btn]:
            btn.setObjectName("menuButton")
            btn.setCheckable(True)
            self.layout.addWidget(btn)

        self.translator_btn.setChecked(True)


class TranslatorApp(QMainWindow):
    """Основной класс приложения переводчика."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Переводчик")
        self.setGeometry(100, 100, *Config.WINDOW_SIZE)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.logic = TranslatorLogic(self)
        self.symbols_popup = SymbolsPopup(self)
        self.about_widget = None
        self.apply_styles() 
        self.setup_ui()

    def setup_ui(self) -> None:
        """Инициализирует пользовательский интерфейс приложения."""
        # Загружаем фоновое изображение
        self.svg_renderer = QSvgRenderer(os.path.join(Config.ASSETS_PATH, "background.svg"))
        self.update_background()

        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Виджет с рамкой
        border_widget = QWidget()
        border_widget.setObjectName("borderWidget")
        self.border_layout = QVBoxLayout(border_widget)
        self.border_layout.setContentsMargins(2, 2, 2, 2)

        # Заголовок окна
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 5, 20, 5)

        title_label = QLabel("Переводчик русский-алеутский")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Кнопка минимизации
        minimize_button = QPushButton("━")
        minimize_button.setObjectName("minimizeButton")
        minimize_button.setFixedSize(Config.BUTTON_SIZE)
        minimize_button.clicked.connect(self.showMinimized)
        header_layout.addWidget(minimize_button)

        # Кнопка максимизации/восстановления
        self.maximize_button = QPushButton("回")
        self.maximize_button.setObjectName("maximizeButton")
        self.maximize_button.setFixedSize(Config.BUTTON_SIZE)
        self.maximize_button.clicked.connect(self.logic.toggle_maximized)
        header_layout.addWidget(self.maximize_button)

        # Кнопка закрытия
        close_button = QPushButton("Х")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(Config.BUTTON_SIZE)
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)

        self.border_layout.addWidget(header_widget)

        # Разделительная линия
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        separator_line.setObjectName("separatorLine")
        self.border_layout.addWidget(separator_line)

        # Панель меню
        self.menu_bar = MenuBar()
        self.menu_bar.translator_btn.clicked.connect(lambda: self.logic.switch_section("translator"))
        self.menu_bar.symbols_btn.clicked.connect(lambda: self.logic.switch_section("symbols"))
        self.menu_bar.about_btn.clicked.connect(lambda: self.logic.switch_section("about"))
        self.border_layout.addWidget(self.menu_bar)

        # Контейнер для основного содержимого
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 10, 20, 15)
        self.border_layout.addWidget(self.content_widget)

        main_layout.addWidget(border_widget)

        # Сетка для полей ввода и вывода
        grid_layout = QGridLayout()
        content_layout.addLayout(grid_layout)

        self.input_label = QLabel(self.logic.source_lang)
        grid_layout.addWidget(self.input_label, 0, 0, 1, 1, Qt.AlignCenter)
        grid_layout.setSpacing(15)

        # Кнопка смены языков
        swap_button = QPushButton()
        swap_button.setObjectName("swapButton")
        swap_button.setFixedSize(Config.BUTTON_SIZE)
        normal_icon, hover_icon = self.load_icon(
            os.path.join(Config.ASSETS_PATH, "exchange_icon.svg"),
            os.path.join(Config.ASSETS_PATH, "exchange_hover_icon.svg"),
            Config.BUTTON_SIZE
        )
        swap_button.setIcon(normal_icon)
        swap_button.setIconSize(Config.BUTTON_SIZE)
        swap_button.enterEvent = lambda event: swap_button.setIcon(hover_icon)
        swap_button.leaveEvent = lambda event: swap_button.setIcon(normal_icon)
        swap_button.clicked.connect(self.logic.swap_languages)
        grid_layout.addWidget(swap_button, 0, 1, 1, 1, Qt.AlignCenter)

        self.output_label = QLabel(self.logic.target_lang)
        grid_layout.addWidget(self.output_label, 0, 2, 1, 1, Qt.AlignCenter)

        # Поле ввода текста
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Введите текст для перевода")
        self.input_field.textChanged.connect(self.logic.on_input_text_changed)
        grid_layout.addWidget(self.input_field, 1, 0, 1, 1)

        # Контейнер для поля вывода
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)

        self.output_field = OutputTextEdit()
        self.output_field.setReadOnly(True)
        self.output_field.setPlaceholderText("Перевод появится здесь")

        # Контейнер для кнопки копирования
        self.copy_container = QWidget(self.output_field)
        self.copy_container.setObjectName("copyContainer")
        self.copy_container.setAttribute(Qt.WA_TranslucentBackground)
        copy_layout = QHBoxLayout(self.copy_container)
        copy_layout.setContentsMargins(0, 0, 0, 5)
        copy_layout.setSpacing(10)

        self.copy_tooltip = QLabel("")
        self.copy_tooltip.setObjectName("copyTooltip")
        self.copy_tooltip.hide()
        copy_layout.addWidget(self.copy_tooltip)

        # Кнопка копирования
        self.copy_button = QPushButton()
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setFixedSize(Config.COPY_BUTTON_SIZE)
        copy_normal_icon, copy_hover_icon = self.load_icon(
            os.path.join(Config.ASSETS_PATH, "copy_icon.svg"),
            os.path.join(Config.ASSETS_PATH, "copy_icon_hover.svg"),
            Config.COPY_BUTTON_SIZE
        )
        self.copy_button.setIcon(copy_normal_icon)
        self.copy_button.setIconSize(Config.COPY_BUTTON_SIZE)
        self.copy_button.enterEvent = lambda event: self.copy_button.setIcon(copy_hover_icon)
        self.copy_button.leaveEvent = lambda event: self.copy_button.setIcon(copy_normal_icon)
        self.copy_button.clicked.connect(self.logic.copy_output_text)
        copy_layout.addWidget(self.copy_button)

        self.output_field.setCopyContainer(self.copy_container)
        output_layout.addWidget(self.output_field)

        # Метка для ошибок
        self.error_label = QLabel("", self.output_field)
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.error_label.setAttribute(Qt.WA_TranslucentBackground)
        self.error_label.hide()

        grid_layout.addWidget(output_container, 1, 2, 1, 1)
        content_layout.addSpacing(10)

        # Layout для кнопок "Перевести" и "Очистить"
        button_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)
        button_layout.addStretch(5)

        self.translate_button = QPushButton("Перевести")
        self.translate_button.setObjectName("translateButton")
        self.translate_button.clicked.connect(lambda checked: self.logic.translate_text())
        button_layout.addWidget(self.translate_button)

        button_layout.addStretch(1)

        self.clear_button = QPushButton("Очистить")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self.logic.clear_fields)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch(5)

        # Устанавливаем одинаковую ширину для кнопок с учётом стилей
        translate_width = self.translate_button.sizeHint().width()
        clear_width = self.clear_button.sizeHint().width()
        max_width = max(translate_width, clear_width)
        self.translate_button.setMinimumWidth(max_width)
        self.clear_button.setMinimumWidth(max_width)
        self.translate_button.setMaximumWidth(max_width)
        self.clear_button.setMaximumWidth(max_width)

        # Метка и область прокрутки для истории переводов
        history_label = QLabel("История переводов")
        content_layout.addWidget(history_label, alignment=Qt.AlignLeft)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFixedHeight(150)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_container = QWidget()
        self.history_layout = QHBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(20, 0, 0, 0)
        self.history_layout.addStretch()
        self.history_scroll.setWidget(self.history_container)
        content_layout.addWidget(self.history_scroll)

    def setup_about_section(self) -> None:
        """Инициализирует секцию 'О проекте' с прокруткой."""
        if not self.about_widget:
            self.about_widget = QWidget()
            self.about_widget.setObjectName("aboutWidget")
            layout = QVBoxLayout(self.about_widget)
            layout.setContentsMargins(20, 20, 20, 20)

            # Создаём QScrollArea для прокрутки
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            layout.addWidget(scroll_area)

            # Контейнер для текста
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(10, 10, 10, 10)

            # Текст "О проекте" из config.py
            text = QLabel(Config.ABOUT_TEXT)
            text.setObjectName("aboutText")
            text.setAlignment(Qt.AlignCenter)
            text.setWordWrap(True)
            content_layout.addWidget(text)

            content_layout.addStretch()
            scroll_area.setWidget(content_widget)

            self.border_layout.insertWidget(3, self.about_widget)

        self.content_widget.hide()
        self.about_widget.show()

    def load_icon(self, normal_svg: str, hover_svg: str, size: tuple [int, int]) -> None:
        """Загружает иконки для кнопок (обычное и при наведении)."""
        normal_pixmap = QPixmap(size)
        normal_pixmap.fill(Qt.transparent)
        QSvgRenderer(normal_svg).render(QPainter(normal_pixmap))

        hover_pixmap = QPixmap(size)
        hover_pixmap.fill(Qt.transparent)
        QSvgRenderer(hover_svg).render(QPainter(hover_pixmap))

        return QIcon(normal_pixmap), QIcon(hover_pixmap)

    def update_background(self) -> None:
        """Обновляет фоновое изображение окна."""
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.svg_renderer.render(painter)
        painter.end()
        palette = self.palette()
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

    def apply_styles(self) -> None:
        """Применяет стили из файла styles.qss."""
        full_path = os.path.abspath(Config.STYLESHEET_PATH)
        with open(Config.STYLESHEET_PATH, "r") as f:
            self.setStyleSheet(f.read())

    def showEvent(self, event: QEvent) -> None:
        """Обрабатывает событие отображения окна."""
        self.output_field.updateCopyContainerPosition()
        self.error_label.setGeometry(0, 0, self.output_field.width(), self.output_field.height())
        super().showEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Обрабатывает событие изменения размера окна."""
        self.update_background()
        self.error_label.setGeometry(0, 0, self.output_field.width(), self.output_field.height())
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает нажатие мыши."""
        self.logic.mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает движение мыши."""
        self.logic.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Обрабатывает отпускание мыши."""
        self.logic.mouseReleaseEvent(event)