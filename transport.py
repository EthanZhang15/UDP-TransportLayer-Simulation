import argparse
import json
from typing import Dict, List, Optional, Tuple
import random
import socket

# Note: In this starter code, we annotate types where
# appropriate. While it is optional, both in python and for this
# course, we recommend it since it makes programming easier.

# The maximum size of the data contained within one packet
payload_size = 1200
# The maximum size of a packet including all the JSON formatting
packet_size = 1500


class Receiver:
    def __init__(self):
        # Initialize a buffer to store received data until it's ready for delivery
        self.buffer = {}
        self.expected_seq = 0

    def data_packet(self, seq_range: Tuple[int, int], data: str) -> Tuple[List[Tuple[int, int]], str]:
        # If the data range is less than expected, send an ack to update the sender
        if(seq_range[0] < self.expected_seq):
            return [(seq_range[0], self.expected_seq)], ""
        
        # Store the received data in the buffer and begin to store the acks
        self.buffer[seq_range[0]] = data
        ack_ranges = [(seq_range[0], seq_range[1])]

        # Check if the data can be delivered to the application
        ready_data = ""
        while self.expected_seq in self.buffer:
            packet = self.buffer[self.expected_seq]
            ready_data += packet
            del self.buffer[self.expected_seq]
            newExpected = self.expected_seq + len(packet)
            ack_ranges.append((self.expected_seq, newExpected))
            self.expected_seq = newExpected  # Increment by the length of the current packet
        
        # Acknowledge the range of sequence numbers received
        return ack_ranges, ready_data

    def finish(self):
        ''' Check if all data has been sent to the application'''
        if self.buffer:
            print("Not all data was sent to the application. There might be an issue.")
        else:
            print("All data was successfully received and delivered.")


class Sender:
    def __init__(self, data_len: int):
        self.data_len = data_len # The total amount of data
        self.next_seq = 0  # The sequence number of the next byte to send
        self.acknowledged = set()  # Set of acknowledged sequence numbers
        self.unacknowledged = set()  # Set of unacknowledged sequence numbers

    def timeout(self):
        ''' Called when the sender times out and needs to retransmit '''
        # Find the smallest unacked seq
        for seq in self.unacknowledged:
            self.next_seq = min(seq, self.next_seq)

    def ack_packet(self, sacks: List[Tuple[int, int]], packet_id: int) -> int:
        ''' Process acknowledgment packets '''
        # Go through the selective ACKs and mark the corresponding packets as acknowledged
        new_acknowledged = 0
        for start, end in sacks:
            for seq in range(start, end, payload_size):
                if seq in self.unacknowledged:
                    self.unacknowledged.remove(seq)
                    self.acknowledged.add(seq)
                    new_acknowledged += 1
        return new_acknowledged

    def send(self, packet_id: int) -> Optional[Tuple[int, int]]:
        ''' Sends the next packet of data '''
        # Check if we've reached the end and have no more data to send
        if self.next_seq >= self.data_len:
            if len(self.unacknowledged) > 0:
                self.timeout()
            else:
                return None

        # Find the next Unacked seq and send it
        while (self.next_seq in self.acknowledged):
            self.next_seq = min(self.next_seq + payload_size, self.data_len)
        end_seq = min(self.next_seq + payload_size, self.data_len)
        self.unacknowledged.add(self.next_seq)
        seq_range = (self.next_seq, end_seq)
        self.next_seq = end_seq
        return seq_range


def start_receiver(ip: str, port: int):
    '''Starts a receiver thread. For each source address, we start a new
    `Receiver` class. When a `fin` packet is received, we call the
    `finish` function of that class.

    We start listening on the given IP address and port. By setting
    the IP address to be `0.0.0.0`, you can make it listen on all
    available interfaces. A network interface is typically a device
    connected to a computer that interfaces with the physical world to
    send/receive packets. The WiFi and ethernet cards on personal
    computers are examples of physical interfaces.

    Sometimes, when you start listening on a port and the program
    terminates incorrectly, it might not release the port
    immediately. It might take some time for the port to become
    available again, and you might get an error message saying that it
    could not bind to the desired port. In this case, just pick a
    different port. The old port will become available soon. Also,
    picking a port number below 1024 usually requires special
    permission from the OS. Pick a larger number. Numbers in the
    8000-9000 range are conventional.

    Virtual interfaces also exist. The most common one is `localhost',
    which has the default IP address of `127.0.0.1` (a universal
    constant across most machines). The Mahimahi network emulator also
    creates virtual interfaces that behave like real interfaces, but
    really only emulate a network link in software that shuttles
    packets between different virtual interfaces. Use `ifconfig` in a
    terminal to find out what interfaces exist in your machine or
    inside a Mahimahi shell

    '''

    receivers: Dict[str, Tuple[Receiver, Any]] = {}
    received_data = ''
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((ip, port))

        while True:
            print("======= Waiting =======")
            data, addr = server_socket.recvfrom(packet_size)
            if addr not in receivers:
                outfile = None  # open(f'rcvd-{addr[0]}-{addr[1]}', 'w')
                receivers[addr] = (Receiver(), outfile)

            received = json.loads(data.decode())
            if received["type"] == "data":
                # Format check. Real code will have much more
                # carefully designed checks to defend against
                # attacks. Can you think of ways to exploit this
                # transport layer and cause problems at the receiver?
                # This is just for fun. It is not required as part of
                # the assignment.
                assert type(received["seq"]) is list
                assert type(received["seq"][0]) is int and type(received["seq"][1]) is int
                assert type(received["payload"]) is str
                assert len(received["payload"]) <= payload_size

                # Deserialize the packet. Real transport layers use
                # more efficient and standardized ways of packing the
                # data. One option is to use protobufs (look it up)
                # instead of json. Protobufs can automatically design
                # a byte structure given the data structure. However,
                # for an internet standard, we usually want something
                # more custom and hand-designed.
                sacks, app_data = receivers[addr][0].data_packet(tuple(received["seq"]), received["payload"])
                # Note: we immediately write the data to file
                # receivers[addr][1].write(app_data)
                print(f"Received seq: {received['seq']}, id: {received['id']}, sending sacks: {sacks}")
                received_data += app_data

                # Send the ACK
                server_socket.sendto(json.dumps({"type": "ack", "sacks": sacks, "id": received["id"]}).encode(), addr)
            elif received["type"] == "fin":
                receivers[addr][0].finish()
                # Check if the file is received and send fin-ack
                if received_data:
                    print("received data (summary): ", received_data[:100], "...", len(received_data))
                    # print("received file is saved into: ", receivers[addr][1].name)
                    server_socket.sendto(json.dumps({"type": "fin"}).encode(), addr)
                    received_data = ''

                del receivers[addr]

            else:
                assert False


def start_sender(ip: str, port: int, data: str, recv_window: int, simloss: float, pkts_to_reorder: int):
    sender = Sender(len(data))

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        # So we can receive messages
        client_socket.connect((ip, port))
        # When waiting for packets when we call receivefrom, we
        # shouldn't wait more than 500ms
        client_socket.settimeout(0.5)

        # Number of bytes that we think are inflight. We are only
        # including payload bytes here, which is different from how
        # TCP does things
        inflight = 0
        packet_id = 0
        wait = False
        send_buf = []

        while True:
            # Do we have enough room in recv_window to send an entire
            # packet?
            if inflight + packet_size < recv_window and not wait:
                seq = sender.send(packet_id)
                got_fin_ack = False
                if seq is None:
                    # We are done sending
                    # print("#######send_buf#########: ", len(send_buf))
                    if send_buf:
                        random.shuffle(send_buf)
                        for p in send_buf:
                            client_socket.send(p)
                        send_buf = []
                    client_socket.send('{"type": "fin"}'.encode())
                    try:
                        print("======= Final Waiting =======")
                        received = client_socket.recv(packet_size)
                        received = json.loads(received.decode())
                        if received["type"] == "ack":
                            client_socket.send('{"type": "fin"}'.encode())
                            continue
                        elif received["type"] == "fin":
                            print(f"Got FIN-ACK")
                            got_fin_ack = True
                            break
                    except socket.timeout:
                        inflight = 0
                        print("Timeout")
                        sender.timeout()
                        exit(1)
                    if got_fin_ack:
                        break
                    else:
                        continue

                elif seq[1] == seq[0]:
                    # No more packets to send until loss happens. Wait
                    wait = True
                    continue

                assert seq[1] - seq[0] <= payload_size
                assert seq[1] <= len(data)
                print(f"Sending seq: {seq}, id: {packet_id}")

                # Simulate random loss before sending packets
                if random.random() < simloss:
                    print("Dropped!")
                else:
                    pkt_str = json.dumps(
                        {"type": "data", "seq": seq, "id": packet_id, "payload": data[seq[0]:seq[1]]}
                    ).encode()
                    # pkts_to_reorder is a variable that bounds the maximum amount of reordering. To disable reordering, set to 1
                    if len(send_buf) < pkts_to_reorder:
                        send_buf += [pkt_str]

                    if len(send_buf) == pkts_to_reorder:
                        # Randomly shuffle send_buf
                        random.shuffle(send_buf)

                        for p in send_buf:
                            client_socket.send(p)
                        send_buf = []

                inflight += seq[1] - seq[0]
                packet_id += 1

            else:
                wait = False
                # Wait for ACKs
                try:
                    print("======= Waiting =======")
                    received = client_socket.recv(packet_size)
                    received = json.loads(received.decode())
                    assert received["type"] == "ack"

                    print(f"Got ACK sacks: {received['sacks']}, id: {received['id']}")
                    if random.random() < simloss:
                        print("Dropped ack!")
                        continue

                    inflight -= sender.ack_packet(received["sacks"], received["id"])
                    assert inflight >= 0
                except socket.timeout:
                    inflight = 0
                    print("Timeout")
                    sender.timeout()


def main():
    parser = argparse.ArgumentParser(description="Transport assignment")
    parser.add_argument("role", choices=["sender", "receiver"], help="Role to play: 'sender' or 'receiver'")
    parser.add_argument("--ip", type=str, required=True, help="IP address to bind/connect to")
    parser.add_argument("--port", type=int, required=True, help="Port number to bind/connect to")
    parser.add_argument("--sendfile", type=str, required=False,
                        help="If role=sender, the file that contains data to send")
    parser.add_argument("--recv_window", type=int, default=15000, help="Receive window size in bytes")
    parser.add_argument("--simloss", type=float, default=0.0,
                        help="Simulate packet loss. Provide the fraction of packets (0-1) that should be randomly dropped")
    parser.add_argument("--pkts_to_reorder", type=int, default=1, help="Number of packets to shuffle randomly")

    args = parser.parse_args()

    if args.role == "receiver":
        start_receiver(args.ip, args.port)
    else:
        if args.sendfile is None:
            print("No file to send")
            return

        with open(args.sendfile, 'r') as f:
            data = f.read()
            start_sender(args.ip, args.port, data, args.recv_window, args.simloss, args.pkts_to_reorder)


if __name__ == "__main__":
    main()
