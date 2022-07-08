import sqlite3


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect("db.sqlite3", check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def convert_results(results):
    return [{k: item[k] for k in item.keys()} for item in results]
