import os
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import mysql.connector
from dotenv import load_dotenv

# Memuat Variabel .env
load_dotenv()

#-------------------------------------------
#Entities
#-------------------------------------------
class User(ComplexModel):
    name = Unicode
    email = Unicode
    role = Unicode
    password = Unicode
    address = Unicode

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
class UserService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Boolean)
    def create_user(ctx, name, email, role, password, address):
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO user (name, email, role, password, address) VALUES (%s, %s, %s, %s, %s)",
                (name, email, role, password, address),
            )
            conn.commit()
            return True
        except Exception as e:
            print("Gagal Menyimpan Data:", e)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @rpc (Integer, _returns=User)
    def get_user(ctx, id):
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "SELECT* FROM user WHERE id=%s",
                (id),
            )
            user = cur.fetchone()
            if user:
                return User(user)
            else:
                return None
        except Exception as e:
            print("Gagal! Gak Tau Kenapa, ", e)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

application = Application(
    [UserService],
    tns="entity.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8002, WsgiApplication(application))
    print("Micro Service running on http://localhost:8002/?wsdl")
    server.serve_forever()