import logging
import queue
import signal
import socket
import threading

from dnslib import CLASS, CNAME, QTYPE, RR, A, DNSError, DNSQuestion, DNSRecord

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MDNS_GROUP = "224.0.0.251"
MDNS_PORT = 5353

requestQueue: queue.Queue[DNSRecord] = queue.Queue()
shutdown_event = threading.Event()

MDNS_ALIAS_FILE = "mdns-aliases"


def get_aliases(filename):
    aliases = []
    try:
        with open(filename) as aliases_file:
            for line in aliases_file:
                aliases.append(line.strip())
    except FileNotFoundError:
        logger.warning(f"Alias file '{filename}' not found.")
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
    m_group = socket.inet_aton(MDNS_GROUP) + socket.INADDR_ANY.to_bytes(
        4, byteorder="big"
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, m_group)

    # Binds the socket to port 5353 for receiving mDNS packets.
    # As the ip address part of this bind is empty string, it will bind to all available interfaces
    sock.bind(("", MDNS_PORT))
    sock.settimeout(5)
    return sock


def get_ip_addr():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        logger.warning("Can't get IP address, defaulting to loopback address.")
        return "127.0.0.1"


def get_hostname():
    try:
        return socket.gethostname()
    except OSError as e:
        logger.warning(f"Error retrieving hostname: {e}")
        return None


class MdnsResponder(threading.Thread):
    def __init__(self, sock: socket.socket):
        super().__init__(name="mdns-responder")
        self.__aliases = get_aliases(MDNS_ALIAS_FILE)
        self.__sock = sock
        self.__ip_addr = get_ip_addr()
        self.__hostname = get_hostname() + ".local."

    def get_type_a_answer(self, question: DNSQuestion) -> RR | None:
        if str(question.qname) in self.__aliases:
            return RR(question.qname, QTYPE.A, CLASS.IN, 60, A(self.__ip_addr))
        return None

    def get_type_cname_answer(self, question: DNSQuestion) -> RR | None:
        if str(question.qname) in self.__aliases:
            return RR(question.qname, QTYPE.CNAME, CLASS.IN, 60, CNAME(self.__hostname))
        return None

    def run(self):
        while not shutdown_event.is_set():
            try:
                query = requestQueue.get(timeout=5)
                questions: list[DNSQuestion] = list(query.questions)
                record = DNSRecord().reply()
                for question in questions:
                    logger.debug(f"Query for: {question.qname}")
                    answer: RR | None = None
                    if self.__hostname:
                        answer = self.get_type_cname_answer(question)
                    elif self.__ip_addr:
                        answer = self.get_type_a_answer(question)
                    if answer:
                        record.add_answer(answer)
                if record.rr:
                    self.__sock.sendto(record.pack(), (MDNS_GROUP, MDNS_PORT))
            except queue.Empty:
                continue
            except OSError as ex:
                logger.warning(f"Socket error in mdns-responder. {ex}")
            except Exception as ex:
                logger.warning(f"Unknown exception in mdns-responder: {ex}")


class MdnsListener(threading.Thread):
    def __init__(self, sock: socket.socket):
        super().__init__(name="mdns-listener")
        self.__sock = sock

    def run(self):
        while not shutdown_event.is_set():
            try:
                data, addr = self.__sock.recvfrom(4096)
                query = DNSRecord.parse(data)
                if query.header.qr == 0:
                    requestQueue.put(query)
            except socket.timeout:
                logger.warning("No mDNS packet received, still listening...")
            except OSError as ex:
                logger.warning(f"Socket error in listener. {ex}")
            except DNSError:
                logger.warning("Failed to decode received data.")
            except Exception as ex:
                logger.warning(f"Unknown exception in mdns-listener: {ex}")


def publish_aliasses():
    aliases = get_aliases(MDNS_ALIAS_FILE)
    for alias in aliases:
        query = DNSRecord().question(alias)
        requestQueue.put(query)


if __name__ == "__main__":
    logger.info(f"Aliases = {get_aliases(MDNS_ALIAS_FILE)}")
    logger.info(f"IP Address = {get_ip_addr()}")
    logger.info(f"Hostname = {get_hostname()}")

    s = create_mdns_socket()
    listener = MdnsListener(s)
    responder = MdnsResponder(s)

    listener.start()
    responder.start()

    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        shutdown_event.set()
        s.close()

    signal.signal(signal.SIGINT, signal_handler)

    publish_aliasses()

    listener.join()
    responder.join()
