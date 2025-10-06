from spyne import Application, rpc, ServiceBase, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class PaymentService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Float)
    def calculate_fare(ctx, pickup, destination):
        # Simulasi jarak berdasarkan panjang string
        distance = abs(len(pickup) - len(destination)) + 5
        fare = distance * 3000.0
        return fare

application = Application(
    [PaymentService],
    tns="payment.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8002, WsgiApplication(application))
    print("Payment Service running on http://localhost:8002/?wsdl")
    server.serve_forever()
