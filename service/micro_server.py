from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

orders_in_queue = {}
    
class PaymentService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Float)
    def calculate_fare(ctx, pickup, destination):
        distance = abs(len(pickup) - len(destination)) + 5
        return distance * 3000.0

application = Application(
    [PaymentService],
    tns="micro.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8001, WsgiApplication(application))
    print("Micro Service running on http://localhost:8001/?wsdl")
    server.serve_forever()
