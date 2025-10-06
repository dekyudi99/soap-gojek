from zeep import Client

ORDER_WSDL = "http://localhost:8000/?wsdl"

client = Client(ORDER_WSDL)

pickup = "Undiksha"
destination = "Pantai Lovina"

order = client.service.request_driver(pickup, destination)

print("Order Summary:")
print(f"Order ID   : {order.orderId}")
print(f"Driver     : {order.driver}")
print(f"Pickup     : {order.pickup}")
print(f"Destination: {order.destination}")
print(f"Fare       : Rp {order.fare}")
