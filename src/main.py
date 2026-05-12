"""Main application entry point"""
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Run the application"""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
