import json
import os
import pandas as pd
import xml.etree.ElementTree as ET
import csv

class Database:
    def __init__(self, name):
        self.name = name
        self.tables = {}

    def create_table(self, table_name, schema):
        """
        Создание новой таблицы в базе данных.
        :param table_name: Название таблицы.
        :param schema: Схема таблицы (словарь с названиями столбцов и их типами).
        """
        if table_name in self.tables:
            raise ValueError(f"Таблица с именем '{table_name}' уже существует.")
        self.tables[table_name] = Table(table_name, schema)

    def get_table(self, table_name):
        """Возвращает таблицу по имени."""
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        return self.tables[table_name]

    def show_structure(self):
        """Показывает структуру базы данных."""
        structure = {"Database": self.name, "Tables": {}}
        for table_name, table in self.tables.items():
            structure["Tables"][table_name] = table.schema
        return structure

    def save_to_file(self, filename):
        """Сохраняет базу данных в файл JSON."""
        data = {
            "name": self.name,
            "tables": {name: table.to_dict() for name, table in self.tables.items()},
        }
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def load_from_file(filename):
        """Загружает базу данных из файла JSON."""
        with open(filename, "r") as file:
            data = json.load(file)
        db = Database(data["name"])
        for table_name, table_data in data["tables"].items():
            table = Table.from_dict(table_data)
            db.tables[table_name] = table
        return db

    def save_database_to_csv(self, directory_path):
        """Сохраняет базу данных в CSV-файлы (каждая таблица — отдельный файл)"""
        os.makedirs(directory_path, exist_ok=True)
        for table_name, table in self.tables.items():
            file_path = os.path.join(directory_path, f"{table_name}.csv")
            data = pd.DataFrame(table.fetch_all())
            data.to_csv(file_path, index=False)

    def save_database_to_txt(self, directory_path):
        """Сохраняет базу данных в текстовые файлы (каждая таблица — отдельный файл)"""
        os.makedirs(directory_path, exist_ok=True)
        for table_name, table in self.tables.items():
            file_path = os.path.join(directory_path, f"{table_name}.txt")
            with open(file_path, "w", encoding="utf-8") as file:
                for record in table.fetch_all():
                    file.write(", ".join(f"{k}: {v}" for k, v in record.items()) + "\n")

    def save_database_to_xml(self, file_path):
        """Сохраняет базу данных в XML-файл"""
        root = ET.Element("database", name=self.name)
        for table_name, table in self.tables.items():
            table_elem = ET.SubElement(root, "table", name=table_name)
            for record in table.fetch_all():
                row_elem = ET.SubElement(table_elem, "row")
                for k, v in record.items():
                    field = ET.SubElement(row_elem, k)
                    field.text = str(v)
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    def save_database_to_excel(self, file_path):
        """Сохраняет базу данных в Excel-файл"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for table_name, table in self.tables.items():
                data = pd.DataFrame(table.fetch_all())
                data.to_excel(writer, sheet_name=table_name, index=False)

    def load_database_from_csv(self, directory_path):
        """Загружает базу данных из CSV-файлов"""
        files = [f for f in os.listdir(directory_path) if f.endswith(".csv")]
        for file in files:
            table_name = os.path.splitext(file)[0]
            file_path = os.path.join(directory_path, file)
            self.load_from_csv(table_name, file_path)

    def load_database_from_txt(self, directory_path):
        """Загружает базу данных из текстовых файлов"""
        files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
        for file in files:
            table_name = os.path.splitext(file)[0]
            file_path = os.path.join(directory_path, file)
            self.load_from_txt(table_name, file_path)

    def load_database_from_xml(self, file_path):
        """Загружает базу данных из XML-файла"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        for table_elem in root.findall("table"):
            table_name = table_elem.get("name")
            schema = {}
            for row in table_elem.findall("row"):
                for field in row:
                    schema[field.tag] = "TEXT"
                break  # Определяем схему по первой строке
            self.create_table(table_name, schema)
            for row in table_elem.findall("row"):
                record = {field.tag: field.text for field in row}
                self.insert_into_table(table_name, record)

    def load_database_from_excel(self, file_path):
        """Загружает базу данных из Excel-файла"""
        data = pd.ExcelFile(file_path, engine='openpyxl')
        for sheet_name in data.sheet_names:
            table_name = sheet_name
            table_data = data.parse(sheet_name)
            schema = {col: "TEXT" for col in table_data.columns}
            self.create_table(table_name, schema)
            for _, row in table_data.iterrows():
                self.insert_into_table(table_name, row.to_dict())

    def insert_into_table(self, table_name, record):
        """Добавляет запись в таблицу."""
        if table_name not in self.tables:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        self.tables[table_name].insert(record)

class Table:
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema  # Схема таблицы: {"col_name": "type"}
        self.data = []  # Список записей

    def insert(self, record):
        """
        Вставляет запись в таблицу.
        :param record: Словарь, где ключи — названия столбцов, значения — данные.
        """
        if not isinstance(record, dict):
            raise ValueError("Запись должна быть словарем.")
        if set(record.keys()) != set(self.schema.keys()):
            raise ValueError("Запись должна содержать все столбцы таблицы.")
        for col, col_type in self.schema.items():
            if not isinstance(record[col], eval(col_type)):
                raise ValueError(f"Столбец '{col}' должен быть типа {col_type}.")
        self.data.append(record)

    def update(self, condition, updates):
        """
        Обновляет записи, соответствующие условию.
        :param condition: Лямбда-функция для фильтрации записей.
        :param updates: Словарь обновлений.
        """
        for record in self.data:
            if condition(record):
                for key, value in updates.items():
                    if key in record:
                        record[key] = value

    def delete(self, condition):
        """
        Удаляет записи, соответствующие условию.
        :param condition: Лямбда-функция для фильтрации записей.
        """
        self.data = [record for record in self.data if not condition(record)]

    def select(self, condition=None, order_by=None, ascending=True):
        """
        Выбирает записи с фильтрацией и сортировкой.
        :param condition: Лямбда-функция для фильтрации (по умолчанию None).
        :param order_by: Поле для сортировки (по умолчанию None).
        :param ascending: Сортировка по возрастанию (по умолчанию True).
        :return: Список записей.
        """
        result = [record for record in self.data if not condition or condition(record)]
        if order_by:
            result.sort(key=lambda x: x[order_by], reverse=not ascending)
        return result

    def fetch_all(self):
        """Возвращает все записи таблицы."""
        return self.data

    def to_dict(self):
        """Возвращает таблицу в виде словаря для сохранения."""
        return {
            "name": self.name,
            "schema": self.schema,
            "data": self.data,
        }

    @staticmethod
    def from_dict(data):
        """Создает таблицу из словаря."""
        table = Table(data["name"], data["schema"])
        table.data = data["data"]
        return table
    
    def generate_report(self, filename, columns=None, format="csv"):
        """
        Генерирует отчет на основе данных таблицы.

        :param filename: Имя файла для сохранения отчета.
        :param columns: Список столбцов для включения в отчет (по умолчанию все).
        :param format: Формат отчета ("csv", "txt" и т.д.).
        """
        if columns is None:
            columns = self.headers  # Использовать все столбцы, если не указано
        
        data = [columns] + [
            [row[col] for col in columns if col in row]
            for row in self.data
        ]
        
        if format == "csv":
            with open(filename, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(data)
        elif format == "txt":
            with open(filename, "w") as file:
                for row in data:
                    file.write("\t".join(map(str, row)) + "\n")
        else:
            raise ValueError("Неподдерживаемый формат отчета")
