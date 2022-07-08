import csv
import sqlite3

from geogame.utils.db import get_db

columns = [
    {"original": "Geoname ID", "new": "geoname_id", "type": "TEXT"},
    {"original": "Name", "new": "name", "type": "TEXT"},
    {"original": "ASCII Name", "new": "ascii_name", "type": "TEXT"},
    {"original": "Alternate Names", "new": "alternate_names", "type": "TEXT"},
    {"original": "Feature Class", "new": "feature_class", "type": "TEXT"},
    {"original": "Feature Code", "new": "feature_code", "type": "TEXT"},
    {"original": "Country Code", "new": "country_code", "type": "TEXT"},
    {"original": "Country name EN", "new": "country_name_en", "type": "TEXT"},
    {"original": "Country Code 2", "new": "country_code_2", "type": "TEXT"},
    {"original": "Admin1 Code", "new": "admin1_code", "type": "TEXT"},
    {"original": "Admin2 Code", "new": "admin2_code", "type": "TEXT"},
    {"original": "Admin3 Code", "new": "admin3_code", "type": "TEXT"},
    {"original": "Admin4 Code", "new": "admin4_code", "type": "TEXT"},
    {"original": "Population", "new": "population", "type": "INTEGER"},
    {"original": "Elevation", "new": "elevation", "type": "INTEGER"},
    {
        "original": "DIgital Elevation Model",
        "new": "digital_elevation_model",
        "type": "TEXT",
    },
    {"original": "Timezone", "new": "timezone", "type": "TEXT"},
    {"original": "Modification date", "new": "modification_date", "type": "TEXT"},
    {"original": "LABEL EN", "new": "label_en", "type": "TEXT"},
    {"original": "Coordinates", "new": "coordinates", "type": "TEXT"},
]
columns_for_create_query = ", \n\t".join(f"'{c['new']}' {c['type']}" for c in columns)
columns_for_query = "', \n\t'".join(c["new"] for c in columns)
placeholders_for_query = ", ".join("?" for _ in columns)


def load_cities():
    con = get_db()
    cur = con.cursor()

    try:
        if cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cities';"
        ).fetchall():
            return

        q = f"CREATE TABLE cities ({columns_for_create_query}, timezone_general TEXT);"
        cur.execute(q)

        with open("../_static/cities_above_1000.csv", "r") as fin:
            dr = csv.DictReader(fin, delimiter=";")
            to_db = []
            for i in dr:
                t = list(i[column["original"]] for column in columns)
                t.append(i["Timezone"].split("/")[0])
                to_db.append(tuple(t))

        iq = f"""
        INSERT INTO cities ('{columns_for_query}', 'timezone_general')
        VALUES ({placeholders_for_query}, ?);
        """
        cur.executemany(
            iq,
            to_db,
        )
        con.commit()
        con.close()
    except sqlite3.OperationalError:
        con.rollback()
