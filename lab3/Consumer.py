from kafka import KafkaConsumer
from kafka.errors import KafkaError
import psycopg2
from psycopg2 import sql, Error as PGError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Dict, Any, List
import signal
import sys
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import json

class DataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"

class ColumnDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=63)
    data_type: DataType
    is_nullable: bool = True
    is_primary_key: bool = False

    @field_validator('name')
    @classmethod
    def validate_column_name(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Column name can only contain alphanumeric characters and underscores')
        if v[0].isdigit():
            raise ValueError('Column name cannot start with a digit')
        return v

class TableSchema(BaseModel):
    table_name: str = Field(..., min_length=1, max_length=63)
    columns: List[ColumnDefinition] = Field(...)

    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Table name can only contain alphanumeric characters and underscores')
        if v[0].isdigit():
            raise ValueError('Table name cannot start with a digit')
        return v

class DataMessage(BaseModel):
    table_schema: TableSchema
    data: List[Dict[str, Any]]
    operation: str = "insert"  # insert, update, upsert

    @field_validator('data')
    @classmethod
    def validate_data(cls, v, info):
        schema = info.data.get('table_schema')
        if schema is None:
            return v
        column_names = {col.name for col in schema.columns}
        for row in v:
            row_columns = set(row.keys())
            extra_columns = row_columns - column_names
            if extra_columns:
                raise ValueError(f"Extra columns in data: {extra_columns}")
            for col_def in schema.columns:
                if col_def.name in row and row[col_def.name] is not None:
                    if col_def.data_type == DataType.INTEGER:
                        if not isinstance(row[col_def.name], int):
                            try:
                                row[col_def.name] = int(row[col_def.name])
                            except:
                                raise ValueError(f"Column {col_def.name} must be integer")
                    elif col_def.data_type == DataType.FLOAT:
                        if not isinstance(row[col_def.name], (int, float)):
                            try:
                                row[col_def.name] = float(row[col_def.name])
                            except:
                                raise ValueError(f"Column {col_def.name} must be float")
                    elif col_def.data_type == DataType.BOOLEAN:
                        if isinstance(row[col_def.name], str):
                            row[col_def.name] = row[col_def.name].lower() in ['true', '1', 'yes']
        return v

    def to_json(self):
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str):
        return cls.model_validate_json(json_str)

KAFKA_BOOTSTRAP_SERVERS: str = "193.23.219.62"
KAFKA_TOPIC: str = "etl_data_topic"


KAFKA_CONSUMER_GROUP: str = "etl_consumer_group"

POSTGRES_HOST: str = "193.23.219.62"
POSTGRES_PORT: str = "5432"
POSTGRES_DB: str = "ila_db"
POSTGRES_USER: str = "jkl"
POSTGRES_PASSWORD: str = "ilajkl"


APP_HOST: str = "0.0.0.0"
APP_PORT: int = 8000
POSTGRES_CONN_STRING = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

class PostgresManager:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = psycopg2.connect(POSTGRES_CONN_STRING)
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("Connected to Postgres")
            self._create_error_log_table()
        except PGError as e:
            print(f"Error connecting to Postgres: {e}")
            raise

    def _create_error_log_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS etl_error_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            table_name VARCHAR(100),
            error_type VARCHAR(100),
            error_message TEXT,
            raw_data TEXT,
            processed BOOLEAN DEFAULT FALSE
        )
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            print("Error log table created or already exists")
        except PGError as e:
            print(f"Error creating error log table: {e}")

    def log_error(self, table_name: str, error_type: str, error_message: str, raw_data: str = None):
        try:
            insert_sql = """
            INSERT INTO etl_error_logs (table_name, error_type, error_message, raw_data)
            VALUES (%s, %s, %s, %s)
            """
            with self.connection.cursor() as cursor:
                cursor.execute(insert_sql, (table_name, error_type, error_message, raw_data))
            print(f"Error logged: {error_type} - {error_message}")
        except PGError as e:
            print(f"Failed to log error: {e}")

    def table_exists(self, table_name: str) -> bool:
        check_sql = """SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(check_sql, (table_name,))
                return cursor.fetchone()[0]
        except PGError as e:
            print(f"Error checking table existence: {e}")
            return False

    def create_table(self, table_schema: Dict[str, Any]):
        table_name = table_schema['table_name']
        columns = table_schema['columns']
        if self.table_exists(table_name):
            print(f"Table {table_name} already exists, skipping creation")
            return
        column_definitions = []
        primary_keys = []
        for col in columns:
            type_mapping = {
                'string': 'VARCHAR(255)',
                'integer': 'INTEGER',
                'float': 'DECIMAL(10, 2)',
                'boolean': 'BOOLEAN',
                'date': 'DATE',
                'datetime': 'TIMESTAMP'
            }
            pg_type = type_mapping.get(col['data_type'], 'VARCHAR(255)')
            nullable = "NULL" if col['is_nullable'] else "NOT NULL"
            column_def = f"{col['name']} {pg_type} {nullable}"
            column_definitions.append(column_def)
            if col.get('is_primary_key', False):
                primary_keys.append(col['name'])
        if primary_keys:
            column_definitions.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
        column_definitions.append("etl_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        column_definitions.append("etl_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        create_sql = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join([sql.SQL(col_def) for col_def in column_definitions])
        )
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_sql)
            print(f"Table {table_name} created successfully")
            self._create_update_trigger(table_name)
        except PGError as e:
            self.log_error(table_name, "CREATE_TABLE_ERROR", f"Error creating table {table_name}: {e}")
            raise Exception(f"Error creating table {table_name}: {e}")

    def _create_update_trigger(self, table_name: str):
        trigger_sql = f"""
        CREATE OR REPLACE FUNCTION update_etl_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.etl_updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        DROP TRIGGER IF EXISTS update_{table_name}_etl_updated_at ON {table_name};
        CREATE TRIGGER update_{table_name}_etl_updated_at
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION update_etl_updated_at_column();
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(trigger_sql)
        except PGError as e:
            print(f"Could not create trigger for {table_name}: {e}")

    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        if not data:
            print(f"No data to insert into {table_name}")
            return
        columns = list(data[0].keys())
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )
        try:
            with self.connection.cursor() as cursor:
                values_list = []
                for row in data:
                    values = []
                    for col in columns:
                        value = row.get(col)
                        if value == 'None' or value == 'null':
                            value = None
                        values.append(value)
                    values_list.append(tuple(values))
                cursor.executemany(insert_sql, values_list)
            print(f"Inserted {len(data)} rows into {table_name}")
        except PGError as e:
            self.log_error(table_name, "INSERT_ERROR", f"Error inserting data into {table_name}: {e}", str(data[:5]))
            print(f"Error inserting data into {table_name}: {e}")

    def process_message(self, data_message: DataMessage):
        try:
            self.create_table(data_message.table_schema.model_dump())
            self.insert_data(
                data_message.table_schema.table_name,
                data_message.data
            )
            print(f"Successfully processed message for table {data_message.table_schema.table_name}")
        except Exception as e:
            print(f"Failed to process message: {e}")

class KafkaConsumerManager:
    def __init__(self, postgres_manager: PostgresManager):
        self.postgres_manager = postgres_manager
        self.consumer = None
        self.running = True
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def connect(self):
        try:
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_CONSUMER_GROUP,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            print(f"Connected to Kafka, subscribing to topic: {KAFKA_TOPIC}")
        except KafkaError as e:
            print(f"Error connecting to Kafka: {e}")

    def shutdown(self, signum, frame):
        print("Shutting down consumer...")
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.postgres_manager.connection:
            self.postgres_manager.connection.close()
        sys.exit(0)

    def consume_messages(self):
        while self.running:
            try:
                message_batch = self.consumer.poll(timeout_ms=1000)
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            print(f"Received message from {topic_partition}, offset: {message.offset}")
                            data_message = DataMessage(**message.value)
                            self.postgres_manager.process_message(data_message)
                            self.consumer.commit()
                        except Exception as e:
                            error_msg = f"Error processing message at offset {message.offset}: {e}"
                            print(error_msg)
                            self.postgres_manager.log_error(
                                table_name=message.value.get('table_schema', {}).get('table_name', 'unknown'),
                                error_type="PROCESSING_ERROR",
                                error_message=str(e),
                                raw_data=json.dumps(message.value, ensure_ascii=False)
                            )
                if not message_batch:
                    print("No new messages, waiting...")
            except KafkaError as e:
                print(f"Kafka error: {e}")

def main():
    print("Starting ETL Consumer...")
    try:
        kafka_manager = KafkaConsumerManager(PostgresManager())
        kafka_manager.connect()
        kafka_manager.consume_messages()
    except Exception as e:
        print(f"Failed to start consumer: {e}")

if __name__ == "__main__":
    main()
