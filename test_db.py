import psycopg

connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="pupilaura",
    user="postgres",
    password="Paul2006"
)

print("Database connection successful!")

connection.close()