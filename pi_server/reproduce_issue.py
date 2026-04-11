import socket
import logging

def check_hostname():
    hostname = socket.gethostname()
    print(f"Hostname: {hostname}")
    return hostname

def simulate_startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("main")
    logger.info(f"Server starting on {socket.gethostname()}")

if __name__ == "__main__":
    check_hostname()
    simulate_startup()
