import logging
import queue
import socket
import threading

from dnslib import DNSRecord, DNSError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MDNS_GROUP = "224.0.0.251"
MDNS_PORT = 5353

queue = queue.Queue()

MDNS_ALIAS_FILE = "mdns-aliases"

def get_aliases(filename):
    aliases = []
    with open(filename) as aliases_file:
        for line in aliases_file:
            aliases.append(line.strip())
    return aliases


def create_mdns_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allows reusing the same IP address and port, even if it's still in TIME_WAIT state (i.e., recently closed).
    # This is important for services that need to restart quickly and bind to the same address without waiting.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Checks whether the socket option "SO_REUSEPORT" is available
    # This is necessary as Linux supports it, but macOS does not.
    if hasattr(socket, "SO_REUSEPORT"):
        # Allows multiple processes or threads to bind to the same port simultaneously.
        # Helps in cases where multiple programs might listen for mDNS responses.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Sets the Time-To-Live (TTL) for multicast packets.
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

    # Controls whether the sender receives its own multicast packets.
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, True)

    # Joins a multicast group so the socket can receive packets sent to the multicast address (224.0.0.251 for mDNS).
    m_group = socket.inet_aton(MDNS_GROUP) + socket.INADDR_ANY.to_bytes(4, byteorder='big')
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, m_group)

    # Binds the socket to port 5353 for receiving mDNS packets.
    # As the ip address part of this bind is empty string, it will bind to all available interfaces
    sock.bind(('', MDNS_PORT))
    return sock


class MdnsResponder(threading.Thread):
    def __init__(self, sock: socket.socket):
        super().__init__(name="mdns-responder")
        self.__aliases = get_aliases(MDNS_ALIAS_FILE)
        self.__sock = sock


    def create_response(self) -> DNSRecord:
        pass

    def run(self):
        pass


class MdnsListener(threading.Thread):
    def __init__(self, sock: socket.socket):
        super().__init__(name="mdns-listener")
        self.__sock = sock

    def run(self):
        while True:
            try:
                data, addr = self.__sock.recvfrom(4096)
                query = DNSRecord.parse(data)
                if query.header.qr == 0:
                    queue.put(query)
            except DNSError:
                logger.warning("Failed to decode received data.")
                continue
            except socket.timeout:
                logger.warning("No mDNS packet received, still listening...")
                continue


def get_ip_addr():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        logger.warning("Can't get ip address, defaulting to loopback address.")
        return "127.0.0.1"


def get_hostname():
    try:
        return socket.gethostname()
    except OSError as e:
        logger.warning(f"Error retrieving hostname: {e}")
        return None


if __name__ == "__main__":
    logger.info(get_aliases(MDNS_ALIAS_FILE))
    # logger.info(get_ip_addr())
    logger.info(get_hostname())
    s = create_mdns_socket()
    MdnsListener(s).start()
    MdnsResponder(s).start()
