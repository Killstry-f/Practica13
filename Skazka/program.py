# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import sqlite3

from login import Ui_Dialog as login_interface
from main import Ui_MainWindow as main_interface
from zakaz import Ui_Dialog as zakaz_interface
from tovar import Ui_Dialog as tovar_interface

DB_NAME = 'Skazka.db'

role = 'Гость'
fio = ''
login = ''

users = [
    ('admin', 'Администратор', 'Администратор', 'admin'),
    ('manager', 'Менеджер', 'Менеджер', 'manager'),
]


def to_display_date(value):
    if value is None:
        return ''
    text = str(value)
    for fmt in ('yyyy-MM-dd', 'dd.MM.yyyy', 'yyyy.MM.dd'):
        date = QDate.fromString(text, fmt)
        if date.isValid():
            return date.toString('dd.MM.yyyy')
    return text


def to_qdate(value):
    if value is None:
        return QDate.currentDate()
    text = str(value)
    for fmt in ('yyyy-MM-dd', 'dd.MM.yyyy', 'yyyy.MM.dd'):
        date = QDate.fromString(text, fmt)
        if date.isValid():
            return date
    return QDate.currentDate()


def to_discount_text(value):
    if value is None or value == '':
        return '0'
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return ('%.2f' % value).rstrip('0').rstrip('.')


class mainWindow(QMainWindow):  # главное окно
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = main_interface()
        self.ui.setupUi(self)

        self.current_role = 'Гость'

        self.setup_texts()
        self.setup_tables()

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

    def setup_texts(self):
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

    def setup_tables(self):
        book_headers = [
            'Код книги',
            'Название книги',
            'Издательство',
            'Автор',
            'Год издания',
            'Цена',
        ]
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setColumnCount(len(book_headers))
        self.ui.tableWidget.setHorizontalHeaderLabels(book_headers)
        self.ui.tableWidget.horizontalHeader().setVisible(True)
        self.ui.tableWidget.verticalHeader().setVisible(False)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableWidget.verticalHeader().setDefaultSectionSize(26)

        order_headers = [
            'Номер заказа',
            'Клиент',
            'Город',
            'Книга',
            'Дата заказа',
            'Количество',
            'Скидка',
        ]
        self.ui.tableWidget_2.clear()
        self.ui.tableWidget_2.setColumnCount(len(order_headers))
        self.ui.tableWidget_2.setHorizontalHeaderLabels(order_headers)
        self.ui.tableWidget_2.verticalHeader().setVisible(False)
        self.ui.tableWidget_2.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget_2.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableWidget_2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget_2.horizontalHeader().setStretchLastSection(True)
        self.ui.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableWidget_2.verticalHeader().setDefaultSectionSize(26)

    def read_zakaz(self):  # заполнение таблицы заказов
        try:
            cursor.execute(
                '''
                SELECT z."Номер_заказа",
                       o."Код_клиента",
                       o."Фирма_производитель",
                       o."Город",
                       k."Код_книги",
                       k."Название_книги",
                       z."Дата_заказа",
                       z."Количество",
                       z."Скидка"
                FROM "Заказы" z
                JOIN "ОптовыеКлиенты" o
                    ON z."ОптовыеКлиенты_Код_клиента" = o."Код_клиента"
                JOIN "Книги" k
                    ON z."Книги_Код_книги" = k."Код_книги"
                ORDER BY z."Номер_заказа"
                '''
            )
            data = cursor.fetchall()
            self.ui.tableWidget_2.setRowCount(len(data))
            for row in range(len(data)):
                values = [
                    data[row]['Номер_заказа'],
                    data[row]['Фирма_производитель'],
                    data[row]['Город'],
                    data[row]['Название_книги'],
                    to_display_date(data[row]['Дата_заказа']),
                    data[row]['Количество'],
                    to_discount_text(data[row]['Скидка']) + '%',
                ]
                for col in range(len(values)):
                    item = QTableWidgetItem(str(values[col]))
                    item.id_zakaz = data[row]['Номер_заказа']
                    self.ui.tableWidget_2.setItem(row, col, item)
            self.zakaz_data = data
            self.ui.tableWidget_2.resizeColumnsToContents()
        except Exception as e:
            print(e)

    def search_tovar(self):  # поиск книг
        try:
            text = self.ui.lineEdit.text().strip()
            filtr = self.ui.comboBox.currentText()
            sql = '''
                SELECT "Код_книги",
                       "Название_книги",
                       "Издательство",
                       "Автор",
                       "Год_издания",
                       "Цена"
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
            like_text = '%' + text + '%'
            sp = [like_text] * 6
            if filtr not in ('Все издательства', ''):
                sql += ' AND "Издательство" = ?'
                sp.append(filtr)
            if self.ui.radioButton_3.isChecked():
                sql += ' ORDER BY "Цена" ASC, "Название_книги"'
            elif self.ui.radioButton.isChecked():
                sql += ' ORDER BY "Цена" DESC, "Название_книги"'
            else:
                sql += ' ORDER BY "Код_книги"'
            cursor.execute(sql, sp)

            data = cursor.fetchall()
            self.ui.tableWidget.setRowCount(len(data))
            for row in range(len(data)):
                values = [
                    data[row]['Код_книги'],
                    data[row]['Название_книги'],
                    data[row]['Издательство'],
                    data[row]['Автор'],
                    data[row]['Год_издания'],
                    data[row]['Цена'],
                ]
                for col in range(len(values)):
                    item = QTableWidgetItem(str(values[col]))
                    item.book_code = data[row]['Код_книги']
                    self.ui.tableWidget.setItem(row, col, item)
            self.tovar_data = data
            self.ui.tableWidget.resizeColumnsToContents()

            try:
                self.ui.comboBox.currentTextChanged.disconnect(self.search_tovar)
            except Exception:
                pass
            cursor.execute(
                '''
                SELECT DISTINCT "Издательство"
                FROM "Книги"
                WHERE IFNULL(TRIM("Издательство"), '') <> ''
                ORDER BY "Издательство"
                '''
            )
            izd = [i[0] for i in cursor.fetchall()]
            self.ui.comboBox.clear()
            self.ui.comboBox.addItem('Все издательства')
            self.ui.comboBox.addItems(izd)
            self.ui.comboBox.setCurrentText(filtr if filtr else 'Все издательства')
            self.ui.comboBox.currentTextChanged.connect(self.search_tovar)
        except Exception as e:
            print(e)

    def set_roles(self, role='Гость', fio='', login=''):  # назначение ролей
        self.current_role = role
        if fio != '':
            self.ui.label_2.setText(fio + ' (' + role + ')')
        else:
            self.ui.label_2.setText(role)

        can_edit = role in ('Менеджер', 'Администратор')
        can_delete = role == 'Администратор'
        show_orders = role in ('Менеджер', 'Администратор')

        self.ui.comboBox.setEnabled(True)
        self.ui.lineEdit.setEnabled(True)
        self.ui.radioButton.setEnabled(True)
        self.ui.radioButton_2.setEnabled(True)
        self.ui.radioButton_3.setEnabled(True)

        self.ui.pushButton.setEnabled(can_edit)
        self.ui.pushButton_2.setEnabled(can_edit)
        self.ui.pushButton_3.setEnabled(can_delete)
        self.ui.pushButton_4.setEnabled(can_delete)
        self.ui.groupBox_2.setVisible(show_orders)

        self.search_tovar()
        if show_orders:
            self.read_zakaz()

    def logout(self):  # выход
        self.hide()
        login_win.ui.lineEdit.setText('')
        login_win.ui.lineEdit_2.setText('')
        login_win.show()

    def add_tovar(self):  # добавление книги
        if self.current_role not in ('Менеджер', 'Администратор'):
            return
        self.tovar_win = tovarWindow()
        self.tovar_win.prepare_add()
        self.tovar_win.exec_()

    def add_zakaz(self):  # добавление заказа
        if self.current_role not in ('Менеджер', 'Администратор'):
            return
        self.zakaz_win = zakazWindow()
        self.zakaz_win.prepare_add()
        self.zakaz_win.exec_()

    def del_tovar(self):  # удаление книги
        if self.current_role != 'Администратор':
            return
        r = self.ui.tableWidget.currentRow()
        if r == -1:
            QMessageBox.critical(self, 'Ошибка', 'Выберите книгу для удаления.', QMessageBox.Ok)
            return
        code = self.ui.tableWidget.item(r, 0).book_code
        cursor.execute(
            'SELECT COUNT(*) FROM "Заказы" WHERE "Книги_Код_книги"=?',
            [code]
        )
        d = int(cursor.fetchone()[0])
        if d == 0:
            try:
                cursor.execute('DELETE FROM "Книги" WHERE "Код_книги"=?', [code])
                conn.commit()
                self.search_tovar()
                QMessageBox.information(self, 'Информация', 'Книга успешно удалена.', QMessageBox.Ok)
            except Exception as e:
                print(e)
                QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранную книгу.', QMessageBox.Ok)
        else:
            QMessageBox.critical(self, 'Ошибка', 'Выбранная книга уже есть в заказе.', QMessageBox.Ok)

    def del_zakaz(self):  # удаление заказа
        if self.current_role != 'Администратор':
            return
        r = self.ui.tableWidget_2.currentRow()
        if r == -1:
            QMessageBox.critical(self, 'Ошибка', 'Выберите заказ для удаления.', QMessageBox.Ok)
            return
        id_zakaz = self.ui.tableWidget_2.item(r, 0).id_zakaz
        try:
            cursor.execute('DELETE FROM "Заказы" WHERE "Номер_заказа"=?', [id_zakaz])
            conn.commit()
            self.read_zakaz()
            QMessageBox.information(self, 'Информация', 'Заказ успешно удалён.', QMessageBox.Ok)
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось удалить выбранный заказ.', QMessageBox.Ok)

    def edit_tovar(self, item):  # изменение данных книги
        if self.current_role not in ('Менеджер', 'Администратор'):
            return
        try:
            code = self.ui.tableWidget.item(item.row(), 0).book_code
            cursor.execute('SELECT * FROM "Книги" WHERE "Код_книги"=?', [code])
            data = cursor.fetchone()
            if data is None:
                return
            self.tovar_win = tovarWindow()
            self.tovar_win.prepare_edit(data)
            self.tovar_win.exec_()
        except Exception as e:
            print(e)

    def edit_zakaz(self, item):  # изменение данных заказа
        if self.current_role not in ('Менеджер', 'Администратор'):
            return
        try:
            id_zakaz = self.ui.tableWidget_2.item(item.row(), 0).id_zakaz
            cursor.execute('SELECT * FROM "Заказы" WHERE "Номер_заказа"=?', [id_zakaz])
            data = cursor.fetchone()
            if data is None:
                return
            self.zakaz_win = zakazWindow()
            self.zakaz_win.prepare_edit(data)
            self.zakaz_win.exec_()
        except Exception as e:
            print(e)


class loginWindow(QDialog):  # окно логирования
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
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

    def log(self):  # вход
        global role, fio, login
        user_login = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text().strip()
        for i in users:
            if i[0] == user_login and i[-1] == password:
                QMessageBox.information(self, 'Информация', 'Вы зашли как ' + i[1], QMessageBox.Ok)
                role = i[2]
                fio = i[1]
                login = i[0]
                main_win.set_roles(role, fio, login)
                self.hide()
                main_win.show()
                return
        QMessageBox.information(
            self,
            'Информация',
            'Логин или пароль не найден. Вы зашли как Гость.',
            QMessageBox.Ok
        )
        role = 'Гость'
        fio = ''
        login = ''
        main_win.set_roles(role, fio, login)
        self.hide()
        main_win.show()

    def log_gost(self):  # вход как гость
        global role, fio, login
        QMessageBox.information(self, 'Информация', 'Вы зашли как Гость.', QMessageBox.Ok)
        role = 'Гость'
        fio = ''
        login = ''
        main_win.set_roles(role, fio, login)
        self.hide()
        main_win.show()


class zakazWindow(QDialog):  # окно добавления/редактирования заказа
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = zakaz_interface()
        self.ui.setupUi(self)

        self.mode = 'add'
        self.order_id = None

        self.book_box = QComboBox(self)
        self.client_box = QComboBox(self)
        self.ui.gridLayout.addWidget(self.book_box, 0, 1, 1, 1)
        self.ui.gridLayout.addWidget(self.client_box, 5, 1, 1, 1)

        self.setup_form()
        self.load_books()
        self.load_clients()

        try:
            self.ui.buttonBox.accepted.disconnect()
            self.ui.buttonBox.rejected.disconnect()
        except Exception:
            pass
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.client_box.currentIndexChanged.connect(self.fill_client_data)

    def setup_form(self):
        self.setWindowTitle('Добавление/редактирование заказа')
        self.ui.label.setText('Книга:')
        self.ui.label_2.setText('Дата заказа:')
        self.ui.label_4.setText('Город:')
        self.ui.label_5.setText('Клиент:')
        self.ui.label_7.setText('Скидка (%):')
        self.ui.label_8.setText('Номер заказа:')
        self.ui.label_9.setText('Количество:')

        self.ui.lineEdit.hide()
        self.ui.lineEdit_5.hide()
        self.ui.label_3.hide()
        self.ui.dateEdit_2.hide()
        self.ui.label_6.hide()
        self.ui.spinBox_2.hide()

        self.ui.lineEdit_4.setReadOnly(True)
        self.ui.lineEdit_8.setReadOnly(True)
        self.ui.lineEdit_7.setText('0')
        self.ui.dateEdit.setDisplayFormat('dd.MM.yyyy')
        self.ui.spinBox.setMinimum(1)
        self.ui.spinBox.setMaximum(100000)

        discount_validator = QDoubleValidator(0.0, 100.0, 2, self)
        discount_validator.setNotation(QDoubleValidator.StandardNotation)
        self.ui.lineEdit_7.setValidator(discount_validator)

    def load_books(self):
        self.book_box.clear()
        cursor.execute(
            '''
            SELECT "Код_книги", "Название_книги"
            FROM "Книги"
            ORDER BY "Название_книги"
            '''
        )
        data = cursor.fetchall()
        for i in data:
            text = str(i['Код_книги']) + ' | ' + str(i['Название_книги'])
            self.book_box.addItem(text, i['Код_книги'])

    def load_clients(self):
        self.client_box.clear()
        cursor.execute(
            '''
            SELECT "Код_клиента", "Фирма_производитель", "Город"
            FROM "ОптовыеКлиенты"
            ORDER BY "Фирма_производитель"
            '''
        )
        data = cursor.fetchall()
        for i in data:
            text = str(i['Код_клиента']) + ' | ' + str(i['Фирма_производитель'])
            self.client_box.addItem(text, i['Код_клиента'])
        self.fill_client_data()

    def fill_client_data(self):
        client_id = self.client_box.currentData()
        if client_id is None:
            self.ui.lineEdit_4.setText('')
            return
        cursor.execute(
            '''
            SELECT "Город"
            FROM "ОптовыеКлиенты"
            WHERE "Код_клиента"=?
            ''',
            [client_id]
        )
        data = cursor.fetchone()
        self.ui.lineEdit_4.setText('' if data is None else str(data['Город']))

    def prepare_add(self):
        self.mode = 'add'
        self.order_id = None
        self.setWindowTitle('Добавление заказа')
        self.ui.lineEdit_8.setText('Авто')
        self.ui.dateEdit.setDate(QDate.currentDate())
        self.ui.spinBox.setValue(1)
        self.ui.lineEdit_7.setText('0')
        self.load_books()
        self.load_clients()

    def prepare_edit(self, data):
        self.mode = 'edit'
        self.order_id = data['Номер_заказа']
        self.setWindowTitle('Редактирование заказа')
        self.load_books()
        self.load_clients()

        self.ui.lineEdit_8.setText(str(data['Номер_заказа']))
        self.ui.dateEdit.setDate(to_qdate(data['Дата_заказа']))
        self.ui.spinBox.setValue(int(data['Количество']))
        self.ui.lineEdit_7.setText(to_discount_text(data['Скидка']))

        book_index = self.book_box.findData(data['Книги_Код_книги'])
        if book_index != -1:
            self.book_box.setCurrentIndex(book_index)
        client_index = self.client_box.findData(data['ОптовыеКлиенты_Код_клиента'])
        if client_index != -1:
            self.client_box.setCurrentIndex(client_index)
        self.fill_client_data()

    def save(self):
        if self.mode == 'edit':
            self.upd()
        else:
            self.add()

    def add(self):  # добавление заказа
        if self.book_box.count() == 0:
            QMessageBox.critical(self, 'Ошибка', 'В базе нет книг для оформления заказа.', QMessageBox.Ok)
            return
        if self.client_box.count() == 0:
            QMessageBox.critical(self, 'Ошибка', 'В базе нет клиентов для оформления заказа.', QMessageBox.Ok)
            return

        try:
            skidka = self.parse_discount()
        except ValueError:
            QMessageBox.critical(self, 'Ошибка', 'Введите корректную скидку от 0 до 100.', QMessageBox.Ok)
            return

        sp = [
            self.client_box.currentData(),
            self.book_box.currentData(),
            self.ui.dateEdit.date().toString('yyyy-MM-dd'),
            self.ui.spinBox.value(),
            skidka,
        ]
        try:
            cursor.execute(
                '''
                INSERT INTO "Заказы"
                (
                    "ОптовыеКлиенты_Код_клиента",
                    "Книги_Код_книги",
                    "Дата_заказа",
                    "Количество",
                    "Скидка"
                )
                VALUES(?,?,?,?,?)
                ''',
                sp
            )
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить заказ.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Заказ успешно добавлен.', QMessageBox.Ok)
        main_win.read_zakaz()
        self.accept()

    def upd(self):  # обновление заказа
        if self.order_id is None:
            return
        try:
            skidka = self.parse_discount()
        except ValueError:
            QMessageBox.critical(self, 'Ошибка', 'Введите корректную скидку от 0 до 100.', QMessageBox.Ok)
            return

        sp = [
            self.client_box.currentData(),
            self.book_box.currentData(),
            self.ui.dateEdit.date().toString('yyyy-MM-dd'),
            self.ui.spinBox.value(),
            skidka,
            self.order_id,
        ]
        try:
            cursor.execute(
                '''
                UPDATE "Заказы"
                SET "ОптовыеКлиенты_Код_клиента"=?,
                    "Книги_Код_книги"=?,
                    "Дата_заказа"=?,
                    "Количество"=?,
                    "Скидка"=?
                WHERE "Номер_заказа"=?
                ''',
                sp
            )
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось редактировать заказ.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Информация о заказе успешно изменена.', QMessageBox.Ok)
        main_win.read_zakaz()
        self.accept()

    def parse_discount(self):
        text = self.ui.lineEdit_7.text().replace(',', '.').strip()
        if text == '':
            text = '0'
        value = float(text)
        if value < 0 or value > 100:
            raise ValueError
        return value


class tovarWindow(QDialog):  # окно добавления/редактирования книги
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = tovar_interface()
        self.ui.setupUi(self)

        self.mode = 'add'
        self.old_code = None

        self.setup_form()

        try:
            self.ui.buttonBox.accepted.disconnect()
            self.ui.buttonBox.rejected.disconnect()
        except Exception:
            pass
        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reject)

    def setup_form(self):
        self.setWindowTitle('Добавление/редактирование книги')

        self.ui.label.setText('Код книги:')
        self.ui.label_2.setText('Название книги:')
        self.ui.label_3.setText('Издательство:')
        self.ui.label_4.setText('Цена:')
        self.ui.label_5.setText('Автор:')
        self.ui.label_9.setText('Год издания:')

        self.ui.label_6.hide()
        self.ui.label_7.hide()
        self.ui.label_8.hide()
        self.ui.label_10.hide()
        self.ui.label_11.hide()

        self.ui.comboBox.hide()
        self.ui.comboBox_2.hide()
        self.ui.spinBox_2.hide()
        self.ui.lineEdit_10.hide()
        self.ui.lineEdit_11.hide()
        self.ui.pushButton.hide()

        self.ui.lineEdit.setValidator(QIntValidator(1, 999999999, self))
        self.ui.spinBox.setMinimum(0)
        self.ui.spinBox.setMaximum(3000)
        self.ui.doubleSpinBox.setDecimals(0)
        self.ui.doubleSpinBox.setMaximum(100000000)

    def prepare_add(self):
        self.mode = 'add'
        self.old_code = None
        self.setWindowTitle('Добавление книги')
        self.ui.lineEdit.setReadOnly(False)
        self.ui.lineEdit.setText('')
        self.ui.lineEdit_2.setText('')
        self.ui.lineEdit_3.setText('')
        self.ui.lineEdit_5.setText('')
        self.ui.spinBox.setValue(0)
        self.ui.doubleSpinBox.setValue(0)

    def prepare_edit(self, data):
        self.mode = 'edit'
        self.old_code = data['Код_книги']
        self.setWindowTitle('Редактирование книги')
        self.ui.lineEdit.setReadOnly(True)
        self.ui.lineEdit.setText(str(data['Код_книги']))
        self.ui.lineEdit_2.setText(str(data['Название_книги']))
        self.ui.lineEdit_3.setText(str(data['Издательство']))
        self.ui.lineEdit_5.setText(str(data['Автор']))
        self.ui.spinBox.setValue(int(data['Год_издания']))
        self.ui.doubleSpinBox.setValue(float(data['Цена']))

    def save(self):
        if self.mode == 'edit':
            self.upd(self.old_code)
        else:
            self.add()

    def add(self):  # добавление книги
        code_text = self.ui.lineEdit.text().strip()
        name = self.ui.lineEdit_2.text().strip()
        izd = self.ui.lineEdit_3.text().strip()
        author = self.ui.lineEdit_5.text().strip()
        year = self.ui.spinBox.value()
        price = int(self.ui.doubleSpinBox.value())
        if code_text == '' or name == '' or izd == '' or author == '' or year == 0 or price == 0:
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        sp = [int(code_text), name, izd, author, year, price]
        try:
            cursor.execute(
                '''
                INSERT INTO "Книги"
                (
                    "Код_книги",
                    "Название_книги",
                    "Издательство",
                    "Автор",
                    "Год_издания",
                    "Цена"
                )
                VALUES(?,?,?,?,?,?)
                ''',
                sp
            )
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось добавить книгу.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Книга успешно добавлена.', QMessageBox.Ok)
        main_win.search_tovar()
        self.accept()

    def upd(self, old_code):  # обновление книги
        if old_code is None:
            return
        name = self.ui.lineEdit_2.text().strip()
        izd = self.ui.lineEdit_3.text().strip()
        author = self.ui.lineEdit_5.text().strip()
        year = self.ui.spinBox.value()
        price = int(self.ui.doubleSpinBox.value())
        if name == '' or izd == '' or author == '' or year == 0 or price == 0:
            QMessageBox.critical(self, 'Ошибка', 'Заполните все поля ввода.', QMessageBox.Ok)
            return
        sp = [name, izd, author, year, price, old_code]
        try:
            cursor.execute(
                '''
                UPDATE "Книги"
                SET "Название_книги"=?,
                    "Издательство"=?,
                    "Автор"=?,
                    "Год_издания"=?,
                    "Цена"=?
                WHERE "Код_книги"=?
                ''',
                sp
            )
            conn.commit()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, 'Ошибка', 'Не удалось редактировать книгу.', QMessageBox.Ok)
            return
        QMessageBox.information(self, 'Информация', 'Информация о книге успешно изменена.', QMessageBox.Ok)
        main_win.search_tovar()
        self.accept()


conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('PRAGMA foreign_keys = ON')

app = QApplication(sys.argv)

app.setStyle(QStyleFactory.create('Fusion'))
pal = app.palette()
pal.setColor(QPalette.Window, QColor('#FFFFFF'))
pal.setColor(QPalette.Button, QColor('#D8F3DC'))
pal.setColor(QPalette.Base, QColor('#F1FFF3'))
app.setPalette(pal)

font = QFont('Times New Roman', 12)
app.setFont(font)

main_win = mainWindow()
login_win = loginWindow()
login_win.show()

result = app.exec_()
cursor.close()
conn.close()
sys.exit(result)
