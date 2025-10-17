import os
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, ComplexModel, Float, Array
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

class Order(ComplexModel):
    id = Integer
    user_id = Integer
    pickup = Unicode
    destination = Unicode
    total = Float
    status = Unicode

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

class OrderService(ServiceBase):
    @rpc(Integer, Unicode, Unicode, Integer, _returns= Boolean)
    def create_order(ctx, user_id, pickup, destination, total):
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders_driver (user_id, pickup, destination, total) VALUES (%s, %s, %s, %s)",
                (user_id, pickup, destination, total),
            )
            conn.commit()
            return True
        except Exception as e:
            print("Gagal Menyimpan!, ", e)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @rpc(_returns=Array(Order))
    def get_all_orders(ctx):
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM orders_driver")
            rows = cur.fetchall()

            orders = []
            for row in rows:
                orders.append(Order(
                    id=row["id"],
                    user_id=row["user_id"],
                    pickup=row["pickup"],
                    destination=row["destination"],
                    total=row["total"],
                    status=row["status"]
                ))
            return orders
        except Exception as e:
            print("Gagal Mengambil Data!, ", e)
            return []
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @rpc(Integer, _returns=Order)
    def get_order_by_id(ctx, order_id):
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM orders_driver WHERE id = %s", (order_id,))
            row = cur.fetchone()

            if row:
                return Order(
                    id=row["id"],
                    user_id=row["user_id"],
                    pickup=row["pickup"],
                    destination=row["destination"],
                    total=row["total"],
                    status=row["status"]
                )
            else:
                return None
        except Exception as e:
            print("Gagal Mengambil Data!, ", e)
            return None
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    @rpc(Unicode, Unicode, Integer, _returns=Boolean)
    def update_order(ctx, column, value, id):
        try:
            allowed_columns = ["driver_id", "status"]
            if column not in allowed_columns:
                raise ValueError("Kolom tidak diizinkan!")

            conn = connectToDatabase()
            cur = conn.cursor()
            
            query = f"UPDATE orders_driver SET {column} = %s WHERE id = %s"
            cur.execute(query, (value, id))
            conn.commit()
            return True
        except Exception as e:
            print("Gagal 😭, ", e)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

application = Application(
    [UserService, OrderService],
    tns="entity.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8002, WsgiApplication(application))
    print("Micro Service running on http://localhost:8002/?wsdl")
    server.serve_forever()