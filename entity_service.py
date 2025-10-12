import os
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, Float, ComplexModel, Array
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import mysql.connector
from dotenv import load_dotenv

# Memuat Variabel .env
load_dotenv()

# Koneksi Ke Database
def connectToDatabase():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
    )

#--------------------------------------------
# Entity Service
#--------------------------------------------

class EntityService(ServiceBase):
    rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _retuns=Boolean)
    def create_user (name, email, role, password, address):
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO user (name, email, role, password, address) VALUES (%s, %s, %s, %s, %s)",
                (name, email, role, password, address),
            )

        except Exception as e:
            print()
        finally:
            print()