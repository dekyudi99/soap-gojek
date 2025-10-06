from spyne import Application, rpc, ServiceBase, Unicode, Float, Integer
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

orders_in_queue = {}

class DriverService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Unicode)
    def assign_driver(ctx, pickup, destination):
        return f"Driver Budi assigned from {pickup} to {destination}"
    
class DriverAppService(ServiceBase):
    @rpc(Integer, Unicode, Unicode, _returns=Unicode)
    def receive_order(ctx, orderId, pickup, destination):
        orders_in_queue[orderId] = {
            "pickup": pickup,
            "destination": destination,
            "status": "pending"
        }
        return "Order received. Waiting for driver."

    @rpc(Integer, _returns=Unicode)
    def confirm_order(ctx, orderId):
        if orderId in orders_in_queue:
            orders_in_queue[orderId]["status"] = "confirmed"
            return "Order confirmed."
        return "Order not found."

    @rpc(Integer, _returns=Unicode)
    def reject_order(ctx, orderId):
        if orderId in orders_in_queue:
            orders_in_queue[orderId]["status"] = "rejected"
            return "Order rejected."
        return "Order not found."

    @rpc(Integer, _returns=Unicode)
    def get_order_status(ctx, orderId):
        if orderId in orders_in_queue:
            return orders_in_queue[orderId]["status"]
        return "not_found"
    
class PaymentService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Float)
    def calculate_fare(ctx, pickup, destination):
        distance = abs(len(pickup) - len(destination)) + 5
        return distance * 3000.0

application = Application(
    [DriverService, PaymentService, DriverAppService],
    tns="micro.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8001, WsgiApplication(application))
    print("Micro Service running on http://localhost:8001/?wsdl")
    server.serve_forever()
