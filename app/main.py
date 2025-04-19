import sys
from PyQt5.QtWidgets import QApplication
from ui import TranslatorApp


if __name__ == "__main__":
    # Создаём экземпляр приложения PyQt5
    application = QApplication(sys.argv)

    # Создаём и отображаем главное окно приложения
    main_window = TranslatorApp()
    main_window.show()

    # Запускаем основной цикл обработки событий и завершаем приложение
    sys.exit(application.exec_())