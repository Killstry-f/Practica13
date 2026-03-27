# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import shutil
import sqlite3
import sys
from PIL import Image

from login import Ui_Dialog as login_interface
from main import Ui_MainWindow as main_interface
from tovar import Ui_Dialog as tovar_interface
from zakaz import Ui_Dialog as zakaz_interface

DB_NAME = 'Skazka.db'
IMAGE_EXTS = ('.png', '.jpg', '.jpeg')
ALL_PUBLISHERS = 'Все издательства'

USERS = {
    'admin': ('Администратор', 'admin'),
    'manager': ('Менеджер', 'manager'),
}

EDIT_ROLES = {'Менеджер', 'Администратор'}
DELETE_ROLES = {'Администратор'}
ORDER_HEADERS = ['Номер заказа', 'Клиент', 'Город', 'Книга', 'Дата заказа', 'Количество', 'Скидка']


def fetch_all(sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchall()


def qdate_from_value(value):
    text = '' if value is None else str(value)
    for fmt in ('yyyy-MM-dd', 'dd.MM.yyyy', 'yyyy.MM.dd'):
        date = QDate.fromString(text, fmt)
        if date.isValid():
            return date
    return QDate.currentDate()


def date_to_text(value):
    return qdate_from_value(value).toString('dd.MM.yyyy') if value else ''


def discount_to_text(value):
    value = 0 if value in (None, '') else float(value)
    return str(int(value)) if value.is_integer() else ('%.2f' % value).rstrip('0').rstrip('.')


def setup_book_table(widget):
    widget.clear()
    widget.setColumnCount(3)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.horizontalHeader().setVisible(False)
    widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    widget.verticalHeader().setVisible(False)
    widget.verticalHeader().setDefaultSectionSize(150)
    widget.verticalHeader().setMinimumSectionSize(150)
    widget.setIconSize(QSize(200, 200))


def setup_table(widget, headers):
    widget.clear()
    widget.setColumnCount(len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.horizontalHeader().setVisible(True)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.verticalHeader().setVisible(False)
    widget.verticalHeader().setDefaultSectionSize(26)


def fill_table(widget, rows, values_fn, attr_name, attr_fn):
    widget.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(values_fn(row)):
            item = QTableWidgetItem(str(value))
            setattr(item, attr_name, attr_fn(row))
            widget.setItem(row_index, col_index, item)
    widget.resizeColumnsToContents()


def import_dir():
    path = os.path.join(os.curdir, 'import')
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def book_image_path(code):
    for ext in IMAGE_EXTS:
        path = os.path.join('import', str(code) + ext)
        if os.path.exists(path):
            return path
    path = os.path.join('import', 'picture.png')
    return path if os.path.exists(path) else ''


def save_book_image(code, source):
    if not source or not os.path.exists(source):
        return
    ext = os.path.splitext(source)[1].lower()
    if ext not in IMAGE_EXTS:
        return
    folder = import_dir()
    target = os.path.join(folder, str(code) + ext)
    for old_ext in IMAGE_EXTS:
        old_path = os.path.join(folder, str(code) + old_ext)
        if os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(target):
            os.remove(old_path)
    if os.path.abspath(source) != os.path.abspath(target):
        shutil.copy(source, target)


class mainWindow(QMainWindow):  # главное окно
    def __init__(self):
        super().__init__()
        self.ui = main_interface()
        self.ui.setupUi(self)
        self.current_role = 'Гость'
        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        self.setWindowTitle('Главное окно')
        self.ui.groupBox.setTitle('Книги')
        self.ui.groupBox_2.setTitle('Заказы')
        self.ui.label_2.setText('Гость')
        self.ui.label_3.setText('Издательства:')
        self.ui.label_4.setText('Поиск:')
        self.ui.label_5.setText('Сортировка по цене:')
        self.ui.radioButton.setText('По убыванию')
        self.ui.radioButton_2.setText('Без сортировки')
        self.ui.radioButton_3.setText('По возрастанию')
        self.ui.pushButton.setText('Добавить книгу')
        self.ui.pushButton_2.setText('Добавить заказ')
        self.ui.pushButton_3.setText('Удалить книгу')
        self.ui.pushButton_4.setText('Удалить заказ')
        setup_book_table(self.ui.tableWidget)
        setup_table(self.ui.tableWidget_2, ORDER_HEADERS)

    def bind_events(self):
        self.ui.action.triggered.connect(self.logout)
        self.ui.pushButton.clicked.connect(self.add_tovar)
        self.ui.pushButton_2.clicked.connect(self.add_zakaz)
        self.ui.pushButton_3.clicked.connect(self.del_tovar)
        self.ui.pushButton_4.clicked.connect(self.del_zakaz)
        self.ui.radioButton.toggled.connect(self.search_tovar)
        self.ui.radioButton_2.toggled.connect(self.search_tovar)
        self.ui.radioButton_3.toggled.connect(self.search_tovar)
        self.ui.lineEdit.textChanged.connect(self.search_tovar)
        self.ui.comboBox.currentTextChanged.connect(self.search_tovar)
        self.ui.tableWidget.itemDoubleClicked.connect(self.edit_tovar)
        self.ui.tableWidget_2.itemDoubleClicked.connect(self.edit_zakaz)

    def selected_attr(self, widget, attr_name, item=None):
        current = widget.item(item.row(), 0) if item else widget.item(widget.currentRow(), 0)
        return getattr(current, attr_name, None) if current else None

    def has_edit_rights(self):
        return self.current_role in EDIT_ROLES

    def has_delete_rights(self):
        return self.current_role in DELETE_ROLES

    def read_zakaz(self):  # заполнение таблицы заказов
        rows = fetch_all(
            '''
            SELECT z."Номер_заказа",
                   o."Фирма_производитель",
                   o."Город",
                   k."Название_книги",
                   z."Дата_заказа",
                   z."Количество",
                   z."Скидка"
            FROM "Заказы" z
            JOIN "ОптовыеКлиенты" o ON z."ОптовыеКлиенты_Код_клиента" = o."Код_клиента"
            JOIN "Книги" k ON z."Книги_Код_книги" = k."Код_книги"
            ORDER BY z."Номер_заказа"
            '''
        )
        fill_table(
            self.ui.tableWidget_2,
            rows,
            lambda row: [
                row['Номер_заказа'],
                row['Фирма_производитель'],
                row['Город'],
                row['Название_книги'],
                date_to_text(row['Дата_заказа']),
                row['Количество'],
                discount_to_text(row['Скидка']) + '%',
            ],
            'order_id',
            lambda row: row['Номер_заказа'],
        )

    def refresh_publishers(self, current_text):
        blocker = QSignalBlocker(self.ui.comboBox)
        publishers = [row[0] for row in fetch_all(
            '''
            SELECT DISTINCT "Издательство"
            FROM "Книги"
            WHERE IFNULL(TRIM("Издательство"), '') <> ''
            ORDER BY "Издательство"
            '''
        )]
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem(ALL_PUBLISHERS)
        self.ui.comboBox.addItems(publishers)
        self.ui.comboBox.setCurrentText(current_text if current_text in publishers else ALL_PUBLISHERS)
        del blocker

    def search_tovar(self):  # поиск книг
        text = '%' + self.ui.lineEdit.text().strip() + '%'
        publisher = self.ui.comboBox.currentText()
        order_sql = {
            self.ui.radioButton_3: ' ORDER BY "Цена" ASC, "Название_книги"',
            self.ui.radioButton: ' ORDER BY "Цена" DESC, "Название_книги"',
        }
        sql = '''
            SELECT "Код_книги", "Название_книги", "Издательство", "Автор", "Год_издания", "Цена"
            FROM "Книги"
            WHERE (
                CAST("Код_книги" AS TEXT) LIKE ?
                OR IFNULL("Название_книги", '') LIKE ?
                OR IFNULL("Издательство", '') LIKE ?
                OR IFNULL("Автор", '') LIKE ?
                OR IFNULL(CAST("Год_издания" AS TEXT), '') LIKE ?
                OR IFNULL(CAST("Цена" AS TEXT), '') LIKE ?
            )
        '''
        params = [text] * 6
        if publisher not in ('', ALL_PUBLISHERS):
            sql += ' AND "Издательство" = ?'
            params.append(publisher)
        sql += next((value for button, value in order_sql.items() if button.isChecked()), ' ORDER BY "Код_книги"')
        rows = fetch_all(sql, params)
        self.ui.tableWidget.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            image_item = QTableWidgetItem()
            image_item.book_code = row['Код_книги']
            image_path = book_image_path(row['Код_книги'])
            if image_path:
                image_item.setIcon(QIcon(image_path))
            text_item = QTableWidgetItem()
            text_item.book_code = row['Код_книги']
            price_item = QTableWidgetItem(str(row['Цена']))
            price_item.book_code = row['Код_книги']
            price_item.setTextAlignment(Qt.AlignCenter)
            label = QLabel()
            label.setTextFormat(Qt.RichText)
            label.setText(
                f'{row["Код_книги"]} | {row["Название_книги"]}<br>'
                f'Автор: {row["Автор"]}<br>'
                f'Издательство: {row["Издательство"]}<br>'
                f'Год издания: {row["Год_издания"]}'
            )
            self.ui.tableWidget.setItem(row_index, 0, image_item)
            self.ui.tableWidget.setItem(row_index, 1, text_item)
            self.ui.tableWidget.setCellWidget(row_index, 1, label)
            self.ui.tableWidget.setItem(row_index, 2, price_item)
        self.refresh_publishers(publisher)

    def set_roles(self, role='Гость', fio='', login=''):  # назначение ролей
        self.current_role = role
        self.ui.label_2.setText(fio + ' (' + role + ')' if fio else role)
        self.ui.pushButton.setEnabled(role in EDIT_ROLES)
        self.ui.pushButton_2.setEnabled(role in EDIT_ROLES)
        self.ui.pushButton_3.setEnabled(role in DELETE_ROLES)
        self.ui.pushButton_4.setEnabled(role in DELETE_ROLES)
        self.ui.groupBox_2.setVisible(role in EDIT_ROLES)
        self.search_tovar()
        if role in EDIT_ROLES:
            self.read_zakaz()

    def logout(self):  # выход
        self.hide()
        login_win.ui.lineEdit.clear()
        login_win.ui.lineEdit_2.clear()
        login_win.show()

    def add_tovar(self):  # добавление книги
        if self.has_edit_rights() and tovarWindow(parent=self).exec_():
            self.search_tovar()

    def add_zakaz(self):  # добавление заказа
        if self.has_edit_rights() and zakazWindow(parent=self).exec_():
            self.read_zakaz()

    def del_tovar(self):  # удаление книги
        code = self.selected_attr(self.ui.tableWidget, 'book_code')
        if not self.has_delete_rights():
            return
        if code is None:
            QMessageBox.critical(self, 'Ошибка', 'Выберите книгу для удаления.', QMessageBox.Ok)
            return
        if fetch_all('SELECT COUNT(*) AS cnt FROM "Заказы" WHERE "Книги_Код_книги"=?', [code])[0]['cnt']:
            QMessageBox.critical(self, 'Ошибка', 'Выбранная книга уже есть в заказе.', QMessageBox.Ok)
            return
        try:
            cursor.execute('DELETE FROM "Книги" WHERE "Код_книги"=?', [code])
            conn.commit()
            self.search_tovar()
            QMessageBox.information(self, 'Информация', 'Книга успешно удалена.', QMessageBox.Ok)
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранную книгу.', QMessageBox.Ok)

    def del_zakaz(self):  # удаление заказа
        order_id = self.selected_attr(self.ui.tableWidget_2, 'order_id')
        if not self.has_delete_rights():
            return
        if order_id is None:
            QMessageBox.critical(self, 'Ошибка', 'Выберите заказ для удаления.', QMessageBox.Ok)
            return
        try:
            cursor.execute('DELETE FROM "Заказы" WHERE "Номер_заказа"=?', [order_id])
            conn.commit()
            self.read_zakaz()
            QMessageBox.information(self, 'Информация', 'Заказ успешно удален.', QMessageBox.Ok)
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранный заказ.', QMessageBox.Ok)

    def edit_tovar(self, item):  # редактирование книги
        code = self.selected_attr(self.ui.tableWidget, 'book_code', item)
        if self.has_edit_rights() and code is not None:
            rows = fetch_all('SELECT * FROM "Книги" WHERE "Код_книги"=?', [code])
            if rows and tovarWindow(rows[0], self).exec_():
                self.search_tovar()

    def edit_zakaz(self, item):  # редактирование заказа
        order_id = self.selected_attr(self.ui.tableWidget_2, 'order_id', item)
        if self.has_edit_rights() and order_id is not None:
            rows = fetch_all('SELECT * FROM "Заказы" WHERE "Номер_заказа"=?', [order_id])
            if rows and zakazWindow(rows[0], self).exec_():
                self.read_zakaz()


class loginWindow(QDialog):  # окно логирования
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = login_interface()
        self.ui.setupUi(self)
        self.setWindowTitle('Авторизация')
        self.ui.lineEdit.setPlaceholderText('Введите логин')
        self.ui.lineEdit_2.setPlaceholderText('Введите пароль')
        self.ui.lineEdit_2.setEchoMode(QLineEdit.Password)
        try:
            self.ui.buttonBox.accepted.disconnect()
            self.ui.buttonBox.rejected.disconnect()
        except Exception:
            pass
        self.ui.buttonBox.accepted.connect(self.log)
        self.ui.buttonBox.rejected.connect(self.log_gost)

    def enter(self, role='Гость', fio='', user_login=''):
        main_win.set_roles(role, fio, user_login)
        self.hide()
        main_win.show()

    def log(self):  # вход
        user_login = self.ui.lineEdit.text().strip()
        user = USERS.get(user_login)
        if user and user[1] == self.ui.lineEdit_2.text().strip():
            QMessageBox.information(self, 'Информация', 'Вы зашли как ' + user[0], QMessageBox.Ok)
            self.enter(user[0], user[0], user_login)
            return
        QMessageBox.information(self, 'Информация', 'Логин или пароль не найден. Вы зашли как Гость.', QMessageBox.Ok)
        self.enter()

    def log_gost(self):  # вход как гость
        QMessageBox.information(self, 'Информация', 'Вы зашли как Гость.', QMessageBox.Ok)
        self.enter()


class zakazWindow(QDialog):  # окно добавления/редактирования заказа
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.ui = zakaz_interface()
        self.ui.setupUi(self)
        self.order_id = None if data is None else data['Номер_заказа']
        self.book_box = QComboBox(self)
        self.client_box = QComboBox(self)
        self.ui.gridLayout.addWidget(self.book_box, 0, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.client_box, 5, 1, 1, 1)
        self.setWindowTitle('Редактирование заказа' if self.order_id else 'Добавление заказа')
        self.load_books()
        self.load_clients()
        self.load_data(data)
        try:
            self.ui.buttonBox.accepted.disconnect()
            self.ui.buttonBox.rejected.disconnect()
        except Exception:
            pass
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.client_box.currentIndexChanged.connect(self.update_city)

    def load_books(self):
        self.book_box.clear()
        for row in fetch_all('SELECT "Код_книги", "Название_книги" FROM "Книги" ORDER BY "Название_книги"'):
            self.book_box.addItem(f'{row["Код_книги"]} | {row["Название_книги"]}', row['Код_книги'])

    def load_clients(self):
        self.client_box.clear()
        for row in fetch_all('SELECT "Код_клиента", "Фирма_производитель", "Город" FROM "ОптовыеКлиенты" ORDER BY "Фирма_производитель"'):
            self.client_box.addItem(f'{row["Код_клиента"]} | {row["Фирма_производитель"]}', row['Код_клиента'])
            self.client_box.setItemData(self.client_box.count() - 1, row['Город'], Qt.UserRole + 1)

    def update_city(self):
        self.ui.lineEdit_4.setText(str(self.client_box.currentData(Qt.UserRole + 1) or ''))

    def load_data(self, data):
        self.ui.lineEdit_8.setText('Авто' if data is None else str(data['Номер_заказа']))
        self.ui.dateEdit.setDate(qdate_from_value(None if data is None else data['Дата_заказа']))
        self.ui.spinBox.setValue(1 if data is None else int(data['Количество']))
        self.ui.lineEdit_7.setText('0' if data is None else discount_to_text(data['Скидка']))
        if data is not None:
            self.book_box.setCurrentIndex(max(0, self.book_box.findData(data['Книги_Код_книги'])))
            self.client_box.setCurrentIndex(max(0, self.client_box.findData(data['ОптовыеКлиенты_Код_клиента'])))
        self.update_city()

    def save(self):
        values = [
            self.client_box.currentData(),
            self.book_box.currentData(),
            self.ui.dateEdit.date().toString('yyyy-MM-dd'),
            self.ui.spinBox.value(),
            float(self.ui.lineEdit_7.text().replace(',', '.').strip() or '0'),
        ]
        sql = '''
            INSERT INTO "Заказы" ("ОптовыеКлиенты_Код_клиента", "Книги_Код_книги", "Дата_заказа", "Количество", "Скидка")
            VALUES(?,?,?,?,?)
        '''
        message = 'Заказ успешно добавлен.'
        if self.order_id is not None:
            sql = '''
                UPDATE "Заказы"
                SET "ОптовыеКлиенты_Код_клиента"=?, "Книги_Код_книги"=?, "Дата_заказа"=?, "Количество"=?, "Скидка"=?
                WHERE "Номер_заказа"=?
            '''
            values.append(self.order_id)
            message = 'Информация о заказе успешно изменена.'
        try:
            cursor.execute(sql, values)
            conn.commit()
            QMessageBox.information(self, 'Информация', message, QMessageBox.Ok)
            self.accept()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось сохранить заказ.', QMessageBox.Ok)


class tovarWindow(QDialog):  # окно добавления/редактирования книги
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.ui = tovar_interface()
        self.ui.setupUi(self)
        self.book_code = None if data is None else data['Код_книги']
        self.setWindowTitle('Редактирование книги' if self.book_code else 'Добавление книги')
        self.ui.lineEdit.setReadOnly(self.book_code is not None)
        self.load_data(data)
        try:
            self.ui.buttonBox.accepted.disconnect()
            self.ui.buttonBox.rejected.disconnect()
        except Exception:
            pass
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.pushButton.clicked.connect(self.select_photo)

    def select_photo(self):  # выбор фотографии
        filename = QFileDialog.getOpenFileName(self, 'Выберите фото', '', 'Photo (*.jpg *.png *.jpeg)')[0]
        if filename:
            with Image.open(filename) as image:
                width, height = image.size
            if width <= 300 and height <= 200:
                self.ui.lineEdit_11.setText(filename)
            else:
                QMessageBox.critical(self, 'Ошибка', 'Размер изображения превышает 300х200 пикселей.', QMessageBox.Ok)

    def load_data(self, data):
        values = ('', '', '', '', 0, 0) if data is None else (
            data['Код_книги'], data['Название_книги'], data['Издательство'], data['Автор'], data['Год_издания'], data['Цена']
        )
        self.ui.lineEdit.setText(str(values[0]))
        self.ui.lineEdit_2.setText(str(values[1]))
        self.ui.lineEdit_3.setText(str(values[2]))
        self.ui.lineEdit_5.setText(str(values[3]))
        self.ui.spinBox.setValue(int(values[4]))
        self.ui.doubleSpinBox.setValue(float(values[5]))
        self.ui.lineEdit_11.setText(book_image_path(values[0]) if values[0] != '' else '')

    def save(self):
        code = self.ui.lineEdit.text().strip()
        name = self.ui.lineEdit_2.text().strip()
        publisher = self.ui.lineEdit_3.text().strip()
        author = self.ui.lineEdit_5.text().strip()
        year = self.ui.spinBox.value()
        price = int(self.ui.doubleSpinBox.value())
        photo = self.ui.lineEdit_11.text().strip()
        if '' in (code, name, publisher, author):
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        sql = '''
            INSERT INTO "Книги" ("Код_книги", "Название_книги", "Издательство", "Автор", "Год_издания", "Цена")
            VALUES(?,?,?,?,?,?)
        '''
        params = [int(code), name, publisher, author, year, price]
        saved_code = int(code)
        message = 'Книга успешно добавлена.'
        if self.book_code is not None:
            sql = '''
                UPDATE "Книги"
                SET "Название_книги"=?, "Издательство"=?, "Автор"=?, "Год_издания"=?, "Цена"=?
                WHERE "Код_книги"=?
            '''
            params = [name, publisher, author, year, price, self.book_code]
            saved_code = self.book_code
            message = 'Информация о книге успешно изменена.'
        try:
            cursor.execute(sql, params)
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось сохранить книгу.', QMessageBox.Ok)
            return
        save_book_image(saved_code, photo)
        QMessageBox.information(self, 'Информация', message, QMessageBox.Ok)
        self.accept()


conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('PRAGMA foreign_keys = ON')

app = QApplication(sys.argv)
app.setStyle(QStyleFactory.create('Fusion'))
palette = app.palette()
palette.setColor(QPalette.Window, QColor('#DCDCDC'))
palette.setColor(QPalette.Button, QColor('#696969'))
palette.setColor(QPalette.Base, QColor('#708090'))
app.setPalette(palette)
app.setFont(QFont('Arial', 12))

main_win = mainWindow()
login_win = loginWindow()
login_win.show()

result = app.exec_()
cursor.close()
conn.close()
sys.exit(result)
