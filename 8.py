import sqlite3
from tkinter import *
from tkinter import ttk
# Устанавливаем соединение с базой данных
connection = sqlite3.connect('tasks.db')
cursor = connection.cursor()
# Создаем таблицу Таsks
cursor.execute('''
CREATE TABLE IF NOT EXISTS Tasks (
id INTEGER PRIMARY KEY,
title TEXT NOT NULL,
status TEXT DEFAULT 'Not Started'
)
''')
# Функция для добавления новой задачи
def add_task(title) :
    cursor.execute('INSERT INTO Tasks (title) VALUES(?)', (title,))
    connection.commit()
# Функция для обновления статуса задачи
def update_task_status (task_id, status):
    cursor.execute('UPDATE Tasks SET status = ? WHERE id = ?', (status, task_id))
    connection.commit()
# Функция для вывода списка задач
def list_tasks():
    cursor.execute('SELECT * FROM Tasks')
    tasks = cursor.fetchall()
    for task in tasks:
        print(task)
# Добавление задачи из Entry
def insert_task():
    add_task(title_var.get())
    title_var.set("")
    list_tasks()
# Обновление статуса выбранной задачи
def change_status():
    selected = table.focus()
    if selected:
        values = table.item(selected, "values")
        task_id = values[0]
        update_task_status(task_id, status_box.get())
        list_tasks()
# Очистка поля
def clear_function():
    title_var.set("")
root = Tk()
root.title("Data Base")
root.geometry("600x400")
#------------
Label(root, text="Data Base").pack()
Label(root, text="input Task").pack()
#_---------
title_var = StringVar(root, value='Подготовить презентацию')
Entry(root, textvariable=title_var).pack()
#---------
Button(root, text="Input in Database", command=insert_task).pack()
Button(root, text="Output from Data Base", command=list_tasks).pack()
#-----------------
Label(root, text="Select Status").pack()
status_box = ttk.Combobox(root, values=["Not Started", "In Progress", "Done"], state="readonly")
status_box.current(0)
status_box.pack()
Button(root, text="Update status", command=change_status).pack()
#--------
table = ttk.Treeview(root, columns=("id", "title", "status"), show="headings")
table.heading("id", text="ID")
table.heading("title", text="Title")
table.heading("status", text="Status")
table.pack(fill=BOTH, expand=1)
#--------
scroll = Scrollbar(root, command=table.yview)
scroll.pack(side=RIGHT, fill=Y)
table.config(yscrollcommand=scroll.set)
#-------
Button(root, text="Clear", command=clear_function).pack(side=LEFT)
Button(root, text="Quit", command=root.destroy).pack(side=RIGHT)
#---------
list_tasks()
# Закрываем соединение
root.mainloop()
connection.close()

