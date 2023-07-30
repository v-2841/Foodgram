import csv
import psycopg2


DB_NAME = 'django'
DB_USER = 'django_user'
DB_PASSWORD = 'mysecretpassword'
DB_HOST = 'localhost'
DB_PORT = '5432'
connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
csv_file_path = 'ingredients.csv'
with open(csv_file_path, 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    # next(csv_reader)  # Первая строка с названиями
    with connection.cursor() as cursor:
        for row in csv_reader:
            name = row[0]
            measurement_unit = row[1]
            cursor.execute(
                "INSERT INTO recipes_ingredientspecification "
                + "(name, measurement_unit) VALUES (%s, %s);",
                (name, measurement_unit)
            )
connection.commit()
connection.close()
print("Данные успешно перенесены в базу данных.")
