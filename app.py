from flask import Flask, render_template, url_for
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_DATABASE"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
    )
    cur = conn.cursor()
    print('PostgreSQL database version:')

    # This is how SQL statements will be executed using cursor's execute function
    cur.execute('SELECT version()')

    db_version = cur.fetchone()
    print(db_version)
    cur.close()
    conn.close()
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
