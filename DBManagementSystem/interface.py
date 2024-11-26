import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from SimpleDB import Database  # Импортируем нашу реализацию СУБД
import os
from tkinter import filedialog

class DBInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Database Management System")
        self.db = None
        self.current_view = "databases"  # Текущий уровень интерфейса: databases, tables, table_data
        self.history = []  # История переходов (для кнопки "Назад")

        # UI компоненты
        self.setup_ui()

    def setup_ui(self):
        """Настраиваем интерфейс"""

        # Верхняя панель
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        self.database_buttons = tk.Frame(self.top_frame)
        tk.Button(self.database_buttons, text="Создать базу данных", command=self.create_database).pack(side=tk.LEFT, padx=5)
        tk.Button(self.database_buttons, text="Загрузить базу данных", command=self.load_database).pack(side=tk.LEFT, padx=5)
        tk.Button(self.database_buttons, text="Сохранить базу данных", command=self.save_database).pack(side=tk.LEFT, padx=5)
        tk.Button(self.database_buttons, text="Экспорт базы данных", command=self.export_database).pack(side=tk.LEFT, padx=5)
        tk.Button(self.database_buttons, text="Импорт базы данных", command=self.import_database).pack(side=tk.LEFT, padx=5)

        self.table_buttons = tk.Frame(self.top_frame)
        tk.Button(self.table_buttons, text="Создать таблицу", command=self.create_table).pack(side=tk.LEFT, padx=5)
        tk.Button(self.table_buttons, text="Назад", command=self.go_back).pack(side=tk.LEFT, padx=5)

        self.data_buttons = tk.Frame(self.top_frame)
        tk.Button(self.data_buttons, text="Добавить запись", command=self.add_record).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Обновить запись", command=self.update_record).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Удалить запись", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Выбрать записи", command=self.select_records).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Сортировать", command=self.sort_records).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Создать отчет", command=self.create_report_interface).pack(side=tk.LEFT, padx=5)
        tk.Button(self.data_buttons, text="Назад", command=self.go_back).pack(side=tk.LEFT, padx=5)

        # Центральная панель для отображения содержимого
        self.tree_view = ttk.Treeview(self.root, columns=[], show="headings")
        self.tree_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree_view.bind("<Double-1>", self.on_double_click)

        self.update_view()

    def update_view(self):
        """Обновляет содержимое интерфейса в зависимости от текущего уровня"""
        self.tree_view.delete(*self.tree_view.get_children())  # Очищаем текущее содержимое
        self.database_buttons.pack_forget()
        self.table_buttons.pack_forget()
        self.data_buttons.pack_forget()

        if self.current_view == "databases":
            # Показ баз данных
            if self.db:
                self.tree_view["columns"] = ["name"]
                self.tree_view.heading("name", text="Базы данных")
                self.tree_view.insert("", "end", values=(self.db.name,))
            self.database_buttons.pack()  # Отображаем кнопки для баз данных
        elif self.current_view == "tables":
            # Показ таблиц внутри базы данных
            if self.db:
                self.tree_view["columns"] = ["name"]
                self.tree_view.heading("name", text="Таблицы")
                for table_name in self.db.tables.keys():
                    self.tree_view.insert("", "end", values=(table_name,))
                self.table_buttons.pack()  # Отображаем кнопки для таблиц
        elif self.current_view == "table_data":
            # Показ данных внутри таблицы
            table_name = self.history[-1]  # Имя таблицы
            try:
                table = self.db.get_table(table_name)  # Получаем объект таблицы
                self.tree_view["columns"] = list(table.schema.keys())  # Настраиваем колонки

                # Добавляем заголовки для каждой колонки
                for col in table.schema.keys():
                    self.tree_view.heading(col, text=col)

                # Заполняем данные
                for record in table.fetch_all():
                    self.tree_view.insert("", "end", values=[record[col] for col in table.schema.keys()])
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные таблицы: {e}")
            self.data_buttons.pack()  # Отображаем кнопки для данных


    def go_back(self):
        """Возвращение на предыдущий уровень"""
        if self.current_view == "table_data":
            self.current_view = "tables"
            self.history.pop()
        elif self.current_view == "tables":
            self.current_view = "databases"
        self.update_view()

    def on_double_click(self, event):
        """Обработка двойного клика для перехода между уровнями"""
        selected_item = self.tree_view.item(self.tree_view.selection())
        if not selected_item:
            return
        selected_value = selected_item["values"][0]

        if self.current_view == "databases":
            self.current_view = "tables"
        elif self.current_view == "tables":
            self.current_view = "table_data"
            self.history.append(selected_value)
        self.update_view()

    def create_database(self):
        """Создаем новую базу данных"""
        name = simpledialog.askstring("Новая база данных", "Введите имя базы данных:")
        if name:
            self.db = Database(name)
            messagebox.showinfo("Успех", f"База данных '{name}' успешно создана!")
        self.update_view()

    def load_database(self):
        """Загружаем базу данных из файла"""
        filename = simpledialog.askstring("Загрузить", "Введите имя файла базы данных (JSON):")
        if filename:
            try:
                self.db = Database.load_from_file(filename)
                messagebox.showinfo("Успех", f"База данных '{self.db.name}' успешно загружена!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить базу данных: {e}")
        self.update_view()

    def save_database(self):
        """Сохраняем базу данных в файл"""
        if not self.db:
            messagebox.showwarning("Предупреждение", "Сначала создайте или загрузите базу данных!")
            return

        filename = simpledialog.askstring("Сохранить", "Введите имя файла для сохранения базы данных (JSON):")
        if filename:
            try:
                self.db.save_to_file(filename)
                messagebox.showinfo("Успех", f"База данных успешно сохранена в файл '{filename}'!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить базу данных: {e}")

    def create_table(self):
        """Создаем новую таблицу"""
        if not self.db:
            messagebox.showwarning("Предупреждение", "Сначала создайте или загрузите базу данных!")
            return

        table_name = simpledialog.askstring("Создать таблицу", "Введите имя таблицы:")
        if not table_name:
            return

        schema = {}
        while True:
            col_name = simpledialog.askstring("Схема таблицы", "Введите имя столбца (или оставьте пустым для завершения):")
            if not col_name:
                break
            col_type = simpledialog.askstring("Схема таблицы", f"Введите тип данных для '{col_name}' (int, str, float):")
            if col_type not in ["int", "str", "float"]:
                messagebox.showwarning("Предупреждение", "Некорректный тип данных! Повторите ввод.")
                continue
            schema[col_name] = col_type

        if schema:
            try:
                self.db.create_table(table_name, schema)
                messagebox.showinfo("Успех", f"Таблица '{table_name}' успешно создана!")
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))
        self.update_view()

    def add_record(self):
        """Добавляем запись в таблицу"""
        if not self.db:
            messagebox.showwarning("Предупреждение", "Сначала создайте или загрузите базу данных!")
            return

        table_name = simpledialog.askstring("Добавить запись", "Введите имя таблицы:")
        if not table_name:
            return

        try:
            table = self.db.get_table(table_name)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return

        record = {}
        for col, col_type in table.schema.items():
            value = simpledialog.askstring("Добавить запись", f"Введите значение для '{col}' ({col_type}):")
            if col_type == "int":
                value = int(value)
            elif col_type == "float":
                value = float(value)
            record[col] = value

        try:
            table.insert(record)
            messagebox.showinfo("Успех", f"Запись успешно добавлена в таблицу '{table_name}'!")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        self.update_view()

    def export_database(self):
        """Экспортирует базу данных в выбранный формат"""
        if not self.db:
            messagebox.showwarning("Предупреждение", "Сначала создайте или загрузите базу данных!")
            return

        file_path = filedialog.asksaveasfilename(filetypes=[
            ("CSV файлы (каталог)", ""),
            ("XML файлы", "*.xml"),
            ("Excel файлы", "*.xlsx"),
            ("Текстовые файлы (каталог)", "")
        ], defaultextension=".xml")

        if not file_path:
            return

        try:
            if file_path.endswith(".xml"):
                self.db.save_database_to_xml(file_path)
            elif file_path.endswith(".xlsx"):
                self.db.save_database_to_excel(file_path)
            elif os.path.isdir(file_path) or not os.path.splitext(file_path)[1]:
                # Если путь указывает на каталог или формат не задан
                self.db.save_database_to_csv(file_path)
            else:
                raise ValueError("Неподдерживаемый формат файла!")

            messagebox.showinfo("Успех", "База данных успешно экспортирована!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать базу данных: {e}")

    def import_database(self):
        """Импортирует базу данных из выбранного формата"""
        file_path = filedialog.askopenfilename(filetypes=[
            ("CSV файлы (каталог)", ""),
            ("XML файлы", "*.xml"),
            ("Excel файлы", "*.xlsx"),
            ("Текстовые файлы (каталог)", "")
        ])

        if not file_path:
            return

        try:
            if file_path.endswith(".xml"):
                self.db.load_database_from_xml(file_path)
            elif file_path.endswith(".xlsx"):
                self.db.load_database_from_excel(file_path)
            elif os.path.isdir(file_path) or not os.path.splitext(file_path)[1]:
                self.db.load_database_from_csv(file_path)
            else:
                raise ValueError("Неподдерживаемый формат файла!")

            messagebox.showinfo("Успех", "База данных успешно импортирована!")
            self.update_view()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать базу данных: {e}")

    def update_record(self):
        """Обновить запись"""
        if not self.db or self.current_view != "table_data":
            messagebox.showwarning("Предупреждение", "Сначала выберите таблицу!")
            return

        table_name = self.history[-1]
        table = self.db.get_table(table_name)

        selected_item = self.tree_view.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для обновления!")
            return

        record_values = self.tree_view.item(selected_item)["values"]
        columns = list(table.schema.keys())
        original_record = {columns[i]: record_values[i] for i in range(len(columns))}

        updates = {}
        for column in columns:
            new_value = simpledialog.askstring("Обновить запись", f"Новое значение для '{column}' (оставьте пустым для пропуска):")
            if new_value:
                updates[column] = eval(table.schema[column])(new_value)

        table.update(lambda r: r == original_record, updates)
        messagebox.showinfo("Успех", "Запись обновлена!")
        self.update_view()

    def delete_record(self):
        """Удалить запись"""
        if not self.db or self.current_view != "table_data":
            messagebox.showwarning("Предупреждение", "Сначала выберите таблицу!")
            return

        table_name = self.history[-1]
        table = self.db.get_table(table_name)

        selected_item = self.tree_view.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления!")
            return

        record_values = self.tree_view.item(selected_item)["values"]
        columns = list(table.schema.keys())
        record_to_delete = {columns[i]: record_values[i] for i in range(len(columns))}

        table.delete(lambda r: r == record_to_delete)
        messagebox.showinfo("Успех", "Запись удалена!")
        self.update_view()

    def select_records(self):
        """Фильтрация записей в таблице"""
        if not self.db or self.current_view != "table_data":
            messagebox.showwarning("Предупреждение", "Сначала выберите таблицу!")
            return

        table_name = self.history[-1]
        table = self.db.get_table(table_name)

        condition = simpledialog.askstring("Фильтрация", "Введите условие для фильтрации (пример: age > 30):")
        if not condition:
            return

        try:
            result = table.select(condition=lambda r: eval(condition, {}, r))
            self.tree_view.delete(*self.tree_view.get_children())
            for record in result:
                self.tree_view.insert("", "end", values=[record[col] for col in table.schema.keys()])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить фильтрацию: {e}")

    def sort_records(self):
        """Сортировка записей в таблице"""
        if not self.db or self.current_view != "table_data":
            messagebox.showwarning("Предупреждение", "Сначала выберите таблицу!")
            return

        table_name = self.history[-1]
        table = self.db.get_table(table_name)

        order_by = simpledialog.askstring("Сортировка", f"Введите имя столбца для сортировки (доступные: {', '.join(table.schema.keys())}):")
        if not order_by or order_by not in table.schema:
            messagebox.showwarning("Предупреждение", "Некорректный столбец для сортировки!")
            return

        ascending = messagebox.askyesno("Порядок сортировки", "Сортировать по возрастанию?")

        try:
            result = table.select(order_by=order_by, ascending=ascending)
            self.tree_view.delete(*self.tree_view.get_children())
            for record in result:
                self.tree_view.insert("", "end", values=[record[col] for col in table.schema.keys()])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить сортировку: {e}")

    def create_report_interface(self):
        """
        Функция для создания отчета через интерфейс.
        """
        if not self.db or self.current_view != "table_data":
            messagebox.showwarning("Предупреждение", "Сначала выберите таблицу!")
            return

        # Получаем имя выбранной таблицы
        table_name = self.history[-1]
        table = self.db.get_table(table_name)

        # Отображаем доступные столбцы
        columns = list(table.schema.keys())  # Это и будут названия столбцов
        print("Доступные столбцы:", ", ".join(columns))

        # Окно для выбора столбцов и формата отчета
        columns_input = simpledialog.askstring("Выбор столбцов", f"Введите столбцы для отчета через запятую (или оставьте пустым для всех):")
        selected_columns = columns_input.split(",") if columns_input else None  # Если пусто - выбираем все столбцы

        format_input = simpledialog.askstring("Выбор формата", "Введите формат отчета (csv или txt):").strip().lower()
        filename = simpledialog.askstring("Имя файла", "Введите имя файла для сохранения отчета (с расширением):").strip()

        if format_input not in ["csv", "txt"]:
            messagebox.showwarning("Ошибка", "Неверный формат отчета!")
            return

        try:
            table.generate_report(filename, columns=selected_columns, format=format_input)
            messagebox.showinfo("Успех", f"Отчет успешно создан: {os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DBInterface(root)
    root.mainloop()
