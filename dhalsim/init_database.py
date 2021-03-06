import argparse
import os
import sqlite3
from pathlib import Path
from dhalsim.py3_logger import get_logger
import yaml
import pandas as pd


class DatabaseInitializer:
    def __init__(self, intermediate_yaml: Path):
        self.intermediate_yaml = intermediate_yaml
        with intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        self.logger = get_logger(self.data['log_level'])
        self.db_path = Path(self.data["db_path"])
        self.db_path.touch(exist_ok=True)
        self.logger.info("Initializing database.")


    def write(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute("""CREATE TABLE plant
                (
                    name  TEXT    NOT NULL,
                    pid   INTEGER NOT NULL,
                    value TEXT,
                    PRIMARY KEY (name, pid)
                );""")

            if "actuators" in self.data:
                for actuator in self.data["actuators"]:
                    initial_state = "0" if actuator["initial_state"].lower() == "closed" else "1"
                    cur.execute("INSERT INTO plant VALUES (?, 1, ?);",
                                (actuator["name"], initial_state,))

            if "plcs" in self.data:
                for plc in self.data["plcs"]:
                    for sensor in plc["sensors"]:
                        cur.execute("INSERT INTO plant VALUES (?, 1, 0);", (sensor,))

            # Creates master_time table if it does not yet exist
            cur.execute("CREATE TABLE master_time (id INTEGER PRIMARY KEY, time INTEGER)")

            # Sets master_time to 0
            cur.execute("REPLACE INTO master_time (id, time) VALUES (1, 0)")

            # Creates sync table
            cur.execute("""CREATE TABLE sync (
                name TEXT NOT NULL,
                flag INT NOT NULL,
                PRIMARY KEY (name)
            );""")

            if "plcs" in self.data:
                for plc in self.data["plcs"]:
                    cur.execute("INSERT INTO sync (name, flag) VALUES (?, 1);",
                                (plc["name"],))

            cur.execute("INSERT INTO sync (name, flag) VALUES ('scada', 1);")

            if "network_attacks" in self.data:
                for attacker in self.data["network_attacks"]:
                    cur.execute("INSERT INTO sync (name, flag) VALUES (?, 1);",
                                (attacker["name"],))

            # Creates attack table
            cur.execute("""CREATE TABLE attack (
                name TEXT NOT NULL,
                flag INT NOT NULL,
                PRIMARY KEY (name)
            );""")
            # Add device attacks to attack table
            if "plcs" in self.data:
                for plc in self.data["plcs"]:
                    if "attacks" in plc:
                        for attack in plc["attacks"]:
                            cur.execute("INSERT INTO attack (name, flag) VALUES (?, 0);",
                                        (attack["name"],))
            # Add network attacks to attack table
            if "network_attacks" in self.data:
                for network_attack in self.data["network_attacks"]:
                    cur.execute("INSERT INTO attack (name, flag) VALUES (?, 0);",
                                (network_attack["name"],))

            conn.commit()

    def drop(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS plant;")
            cur.execute("DROP TABLE IF EXISTS master_time;")
            cur.execute("DROP TABLE IF EXISTS sync;")
            cur.execute("DROP TABLE IF EXISTS attack;")
            conn.commit()

    def print(self):
        with sqlite3.connect(self.db_path) as conn:
            self.logger.debug(pd.read_sql_query("SELECT * FROM plant;", conn))
            self.logger.debug(pd.read_sql_query("SELECT * FROM master_time;", conn))
            self.logger.debug(pd.read_sql_query("SELECT * FROM sync;", conn))
            self.logger.debug(pd.read_sql_query("SELECT * FROM attack;", conn))


def is_valid_file(file_parser, arg):
    if not os.path.exists(arg):
        file_parser.error(arg + " does not exist.")
    else:
        return arg
