import websockets
import websockets.exceptions
print(f"Websockets version: {websockets.version}")
print(f"Exceptions: {dir(websockets.exceptions)}")
try:
    from websockets.exceptions import InvalidStatusCode
    print("InvalidStatusCode found in exceptions")
except ImportError:
    print("InvalidStatusCode NOT found in exceptions")

try:
    from websockets.exceptions import InvalidStatus
    print("InvalidStatus found in exceptions")
except ImportError:
    print("InvalidStatus NOT found in exceptions")
