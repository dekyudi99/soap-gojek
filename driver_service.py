from spyne import Application, rpc, ServiceBase, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class DriverService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Unicode)
    def assign_driver(ctx, pickup, destination):
        return f"Driver Budi assigned from {pickup} to {destination}"

application = Application(
    [DriverService],
    tns="driver.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8001, WsgiApplication(application))
    print("Driver Service running on http://localhost:8001/?wsdl")
    server.serve_forever()
