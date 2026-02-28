import json
import csv
import re
import uuid
import time
from datetime import datetime

from kafka import KafkaProducer


class ETLProducer:
    def __init__(self, bootstrap_servers='195.209.210.13:9092'):
        try:
            print(f"Подключение к Kafka серверу: {bootstrap_servers}")
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                request_timeout_ms=10000,
                retries=3
            )
            self.topic = 'etl_data_topic'
            print("Подключение к Kafka успешно")
        except Exception:
            print(f"Ошибка подключения")

    def validate_table_name(self, table_name):
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        if not re.match(pattern, table_name):
            raise ValueError(f"Недопустимое имя таблицы: '{table_name}'. ")
        return True

    def validate_columns(self, columns):
        validated_columns = []
        for col in columns:
            pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
            if not re.match(pattern, col):
                raise ValueError(f"Недопустимое имя столбца: '{col}'. ")
            validated_columns.append(col)
        return validated_columns

    def validate_row(self, row, column_count):
        if len(row) != column_count:
            raise ValueError(f"Количество значений ({len(row)}) не совпадает с количеством столбцов ({column_count})")
        return row

    def row_to_int(self, row):
        new_row = []
        for i in row:
            try:
                new_row.append(int(i))
            except Exception:
                new_row.append(i)
        return new_row

    def get_manual_input(self):
        try:
            table_name = input("Введите название таблицы: ")
            self.validate_table_name(table_name)

            columns_input = input("Введите имена столбцов через запятую, например, id,name,age: ")
            columns = [i.strip() for i in columns_input.split(',')]
            if not columns:
                raise ValueError("Необходимо указать хотя бы один столбец")
            columns = self.validate_columns(columns)

            print("\nВведите данные построчно.")
            print("Например, вот так: 1,Иван Иванов,25")
            print("Чтобы закончить ввод введите 0")

            data = []
            row_num = 1
            row_input = input(f"Строка {row_num}: ").strip()
            while row_input != '0':
                row_values = self.row_to_int([i.strip() for i in row_input.split(',')])
                validated_row = self.validate_row(row_values, len(columns))
                data.append(validated_row)
                row_num += 1
                row_input = input(f"Строка {row_num}: ").strip()
            if not data:
                raise ValueError("Не введено ни одной строки данных")

            return {
                'table_name': table_name,
                'columns': columns,
                'data': data,
                'source': 'manual'
            }

        except Exception:
            print(f"Ошибка ввода")
            return None

    def load_from_csv(self, file_path):
        try:
            file_path = file_path.replace('"', "")
            table_name = input("Введите название таблицы: ").strip()
            self.validate_table_name(table_name)

            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                columns = self.validate_columns(next(reader)[0].split(';'))
                data = []
                for row in reader:
                    try:
                        row_to_check = self.row_to_int([i.strip() for i in row[0].split(';')])
                        validated_row = self.validate_row(row_to_check, len(columns))
                        data.append(validated_row)
                    except ValueError as e:
                        print(f"Строка '{row}' пропущена из-зи ошибок в ней")
                        continue

            if not data:
                raise ValueError("Файл не содержит данных (кроме заголовков)")

            return {
                'table_name': table_name,
                'columns': columns,
                'data': data,
                'source': 'csv',
                'file_path': file_path
            }

        except FileNotFoundError:
            print(f"Ошибка: Файл '{file_path}' не найден")
        except Exception as exp:
            print(f"Ошибка: {exp}")
        return None

    def load_from_json(self, file_path):
        try:
            file_path = file_path.replace('"', "")
            table_name = input("Введите название таблицы: ").strip()
            self.validate_table_name(table_name)

            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            if not json_data:
                raise ValueError("JSON файл не содержит данных")

            columns_to_validate = list(json_data[0].keys())
            columns = self.validate_columns(columns_to_validate)

            data = []
            for i in json_data:
                try:
                    row_to_check = self.row_to_int([i[col] for col in columns])
                    validated_row = self.validate_row(row_to_check, len(columns))
                    data.append(validated_row)
                except ValueError as e:
                    print(f"Строка '{row_to_check}' пропущена из-зи ошибок в ней")
                    continue

            if not data:
                raise ValueError("Не найдено данных для обработки")

            return {
                'table_name': table_name,
                'columns': columns,
                'data': data,
                'source': 'json',
                'file_path': file_path
            }

        except FileNotFoundError:
            print(f"Ошибка: Файл '{file_path}' не найден")
        except Exception as exp:
            print(f"Ошибка: {exp}")
        return None


    def send_to_kafka(self, message):
        try:
            # Преобразование формата под Consumer
            formatted_message = {
                "table_schema": {
                    "table_name": message['table_name'],
                    "columns": [
                        {"name": col, "data_type": "string"}  # или определяйте тип
                        for col in message['columns']
                    ]
                },
                "data": [
                    dict(zip(message['columns'], row))
                    for row in message['data']
                ],
                "operation": "insert"
            }

            formatted_message['message_id'] = str(uuid.uuid4())
            formatted_message['timestamp'] = datetime.now().isoformat()

            print(f"\nОтправляю данные...")
            self.producer.send(self.topic, value=formatted_message).get(timeout=10)
            print("Данные успешно отправлены!")
            return True

        except Exception as e:
            print(f"Ошибка при отправке в Kafka: {e}")
            return False

    def show_main_menu(self):
        print("---------------------")
        print("1. Ввести данные вручную")
        print("2. Загрузить из CSV файла")
        print("3. Загрузить из JSON файла")
        print("4. Выход")
        print("---------------------")

    def run(self):
        self.show_main_menu()
        choice = input("\nВведите номер команды из списка выше: ")
        while choice != 4:
            if choice == '1':
                message = self.get_manual_input()
                print(message)
                if message:
                    self.send_to_kafka(message)

            elif choice == '2':
                file_path = input("Введите путь к CSV файлу: ")
                if file_path:
                    message = self.load_from_csv(file_path)
                    print(message)
                    if message:
                        self.send_to_kafka(message)

            elif choice == '3':
                file_path = input("Введите путь к JSON файлу: ")
                if file_path:
                    message = self.load_from_json(file_path)
                    print(message)
                    if message:
                        self.send_to_kafka(message)

            choice = input("\nВведите номер команды из списка выше: ")


def main():
    kafka_server = '193.23.219.62:9092'
    producer = ETLProducer(bootstrap_servers=kafka_server)
    producer.run()


if __name__ == "__main__":
    main()
