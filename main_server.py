from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from zeep import Client

# Models
class OrderSummary(ComplexModel):
    orderId = Integer
    driver = Unicode
    fare = Float
    pickup = Unicode
    destination = Unicode

# Microservice endpoints
DRIVER_WSDL = "http://localhost:8001/?wsdl"
PAYMENT_WSDL = "http://localhost:8002/?wsdl"

class OrderService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=OrderSummary)
    def request_driver(ctx, pickup, destination):
        # Panggil Driver Service
        driver_client = Client(DRIVER_WSDL)
        driver_assigned = driver_client.service.assign_driver(pickup, destination)

        # Panggil Payment Service
        payment_client = Client(PAYMENT_WSDL)
        fare = payment_client.service.calculate_fare(pickup, destination)

        # Buat Order Summary
        return OrderSummary(
            orderId=1,
            driver=driver_assigned,
            fare=fare,
            pickup=pickup,
            destination=destination
        )

application = Application(
    [OrderService],
    tns="order.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8000, WsgiApplication(application))
    print("Order Service running on http://localhost:8000/?wsdl")
    server.serve_forever()
