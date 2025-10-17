from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, ComplexModel, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from zeep import Client
import time, os, mysql.connector, jwt, datetime
from dotenv import load_dotenv

# Memuat Variabel .env
load_dotenv()

class ServiceResponse(ComplexModel):
    success = Boolean
    message = Unicode
    token = Unicode
    
class OrderSummary(ComplexModel):
    DriverId = Integer
    fare = Float
    pickup = Unicode
    destination = Unicode
    Status = Unicode

# Koneksi Ke Database
def connectToDatabase():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
    )

MICRO_WSDL = "http://localhost:8001/?wsdl"
ENTITY_WSDL = "http://localhost:8002/?wsdl"

micro_client = Client(MICRO_WSDL)
entity_client = Client(ENTITY_WSDL)

#--------------------------------------------
# Utility Service (Autentikasi)
#--------------------------------------------
class AuthService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def register(ctx, name, email, role, password, address):
        try:
            entity_client.service.create_user(name, email, role, password, address)
            return "Register Berhasil, Silakan login!"
        except Exception as e:
            print("Yang jelas gagal: ", e)
    
    @rpc(Unicode, Unicode, _returns=ServiceResponse)
    def login(ctx, email, password):
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM user WHERE email=%s AND password=%s",
                (email, password),
            )
            user = cur.fetchone()
            if user:
                payload = {
                    "user_id": user["id"],
                    "email": user["email"],
                    "role": user["role"],
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                }
                token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
                return ServiceResponse(success=True, message="Login Berhasil!", token=token)
            else:
                return ServiceResponse(success=False, message="Login Gagal!", token="")
        except Exception as e:
            print("YANG JELAS GAGAL, JANGAN TANYA KENAPA GAGAL!. ", e)
            return ServiceResponse(success=False, message=f"Terjadi kesalahan: {str(e)}", token="")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def verify_token(token):
        try:
            data = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            return True, data
        except jwt.ExpiredSignatureError:
            return False, "Token kadaluarsa."
        except jwt.InvalidTokenError:
            return False, "Token tidak valid."

#--------------------------------------------
# Task Service (Order Service)
#--------------------------------------------
class OrderService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, _returns=OrderSummary)
    def request_driver(ctx, token, pickup, destination):
        valid, data = AuthService.verify_token(token)
        if valid:
            try:
                conn = connectToDatabase()
                cur = conn.cursor(dictionary=True)
                cur.execute(
                    "SELECT * FROM user WHERE id=%s", (data["user_id"],)
                )
                user = cur.fetchone()

                fare = int(micro_client.service.calculate_fare(pickup, destination))

                createSuccess = entity_client.service.create_order(user["id"], pickup, destination, fare)
                if createSuccess:
                    return OrderSummary(fare=fare, pickup=pickup, destination=destination)
            except Exception as e:
                print(e)
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
    
    @rpc(Unicode, Unicode, Integer, _returns=Boolean)
    def konfirmasi_order(ctx, token, confirm, order_id):
        valid, data = AuthService.verify_token(token)
        if valid:
            try:
                entity_client.service.update_order("driver_id", data["user_id"], order_id)
                entity_client.service.update_order("status", confirm, order_id)
                return True
            except Exception as e:
                print("Error konfirmasi_order:", e)
                return False
        else:
            print("Token tidak valid.")
            return False


application = Application(
    [AuthService, OrderService],
    tns="order.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8000, WsgiApplication(application))
    print("Main Server running on http://localhost:8000/?wsdl")
    server.serve_forever()
