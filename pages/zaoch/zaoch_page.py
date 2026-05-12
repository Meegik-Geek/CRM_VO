from PyQt5.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QPushButton, QSplitter, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFont
from pages.zaoch.input_applicant_zaoch import InputApplicantZaoch
from pages.zaoch.input_sprava_zaoch import InputSpravaZaoch
from pages.zaoch.input_pilga_zaoch import InputPilgaZaoch
from pages.zaoch.druk_document_zaoch import DrukDocumentZaoch
from pages.zaoch.list_vstupnik_zaoch import ListVstupnikZaoch

class InputZaochPage(QMainWindow):
    def __init__(self):
        super(InputZaochPage, self).__init__()
        self.setWindowTitle("CRM Вступ.Офіс - Введення вступників заочної форми навчання")
        self.setGeometry(0, 0, 1300, 800)
        self.showMaximized()

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        self.table_list = QListWidget()
        self.table_list.setObjectName("navList")

        self.add_section("Форми (заочна)", bold=True)
        self.add_menu_item("Головна")
        self.add_menu_item("Ввід нового вступника")
        self.add_menu_item("Ввід особової справи")
        self.add_menu_item("Ввід пільги")
        self.add_menu_item("Друк документів")
        self.add_menu_item("Список вступників")

        splitter.addWidget(self.table_list)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel); self.right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([180, 800])

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)

        self.table_list.itemClicked.connect(self.on_item_clicked)
        self.table_list.setCurrentRow(1)
        self.on_item_clicked(self.table_list.item(1))

    def add_section(self, name, bold=False):
        section = QListWidgetItem(name)
        section.setFlags(Qt.NoItemFlags)
        font = QFont()
        font.setBold(bold)
        section.setFont(font)
        section.setTextAlignment(Qt.AlignCenter)
        self.table_list.addItem(section)

    def add_menu_item(self, name):
        item = QListWidgetItem(name)
        item.setFont(QFont("Arial", 12))
        item.setTextAlignment(Qt.AlignLeft)
        self.table_list.addItem(item)

    def clear_right_layout(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_item_clicked(self, item):
        selected_text = item.text()
        self.clear_right_layout()

        if selected_text == "Головна":
            self.show_default_buttons()
        elif selected_text == "Ввід нового вступника":
            self.show_new_applicant_form()
        elif selected_text == "Ввід особової справи":
            self.show_new_sprava_form()
        elif selected_text == "Ввід пільги":
            self.show_new_pilga_form()
        elif selected_text == "Друк документів":
            self.show_print_documents_form()
        elif selected_text == "Список вступників":
            self.show_applicant_list()

    def show_default_buttons(self):
        label = QLabel("Заочна форма навчання", self)
        label.setObjectName("titleLabel")
        label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(label)

        self.button1 = QPushButton("Ввід нового вступника", self)
        self.button1.setObjectName("navButton")
        self.button2 = QPushButton("Друк документів", self)
        self.button2.setObjectName("navButton")
        self.button3 = QPushButton("На Головну", self)
        self.button3.setObjectName("greenButton")

        for button in [self.button1, self.button2, self.button3]:
            button.setFixedWidth(430)
            button.setCursor(QCursor(Qt.PointingHandCursor))
            self.right_layout.addWidget(button)

        self.right_layout.setSpacing(25)
        self.right_layout.setAlignment(Qt.AlignCenter)

        self.button1.clicked.connect(lambda: self.select_menu_item(2))
        self.button2.clicked.connect(lambda: self.select_menu_item(5))
        self.button3.clicked.connect(self.close)
    def select_menu_item(self, row):
        self.table_list.setCurrentRow(row)
        self.on_item_clicked(self.table_list.item(row))

    def show_new_applicant_form(self):
        self.clear_right_layout()
        applicant_form = InputApplicantZaoch()
        self.right_layout.addWidget(applicant_form)

    def show_new_sprava_form(self):
        self.clear_right_layout()
        applicant_form = InputSpravaZaoch()
        self.right_layout.addWidget(applicant_form)

    def show_new_pilga_form(self):
        self.clear_right_layout()
        applicant_form = InputPilgaZaoch()
        self.right_layout.addWidget(applicant_form)

    def show_print_documents_form(self):
        self.clear_right_layout()
        applicant_form = DrukDocumentZaoch()
        self.right_layout.addWidget(applicant_form)

    def show_applicant_list(self):
        self.clear_right_layout()
        applicant_form = ListVstupnikZaoch()
        self.right_layout.addWidget(applicant_form)