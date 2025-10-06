from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from zeep import Client
import time

class OrderSummary(ComplexModel):
    orderId = Integer
    driver = Unicode
    fare = Float
    pickup = Unicode
    destination = Unicode

MICRO_WSDL = "http://localhost:8001/?wsdl"
DRIVER_WSDL = "http://localhost:8002/?wsdl"

class OrderService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=OrderSummary)
    def request_driver(ctx, pickup, destination):
        micro_client = Client(MICRO_WSDL)

        fare = micro_client.service.calculate_fare(pickup, destination)
        order_id = 1

        micro_client.service.receive_order(order_id, pickup, destination)

        while True:
            status = micro_client.service.get_order_status(order_id)

            if status == "confirmed":
                driver_assigned = micro_client.service.assign_driver(pickup, destination)
                return OrderSummary(
                    orderId=order_id,
                    driver=driver_assigned,
                    fare=fare,
                    pickup=pickup,
                    destination=destination
                )

            elif status == "rejected":
                return OrderSummary(
                    orderId=order_id,
                    driver="No driver available",
                    fare=0.0, pickup=pickup,
                    destination=destination
                )

            print("Waiting for driver confirmation...")
            time.sleep(2)


application = Application(
    [OrderService],
    tns="order.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8000, WsgiApplication(application))
    print("Main Server running on http://localhost:8000/?wsdl")
    server.serve_forever()
