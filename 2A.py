import sqlite3
# Устанавливаем соединение с базой данных
connection = sqlite3.connect('my database.db')
cursor = connection.cursor()
# Создаем индекс для столбца "email"
cursor.execute('CREATE INDEX idx email ON Users (email) ')
# Coxpaняем изменения и закрываем соединение
connection.commit( )
connection.close()
