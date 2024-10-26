Custom Transport Layer Protocol
This project implements a custom transport layer protocol in Python over UDP, providing reliable data transfer between a sender and a receiver. The protocol mimics some of the functionalities of TCP, such as segmentation, acknowledgment, and retransmission of lost packets. This project was completed as part of a network programming assignment.

Table of Contents
Project Overview
Features
Requirements
Setup
Usage
Testing
Notes
Project Overview
In this project, a transport layer program ensures reliable data delivery using a sender-receiver model. The sender transmits a large message in segments (packets) to the receiver over an unreliable network link, where packets may be delayed, lost, or received out of order. The receiver acknowledges received packets and requests retransmission of any missing ones. Key functionalities include flow control through a constant receive window and (optionally) handling packet reordering.

Features
Reliable Data Transfer: Ensures message integrity even with packet loss, delay, and reordering.
Selective Acknowledgments: Allows the sender to identify and resend only missing packets.
Flow Control: Limits the number of in-flight packets to manage network load and receiver memory.
Congestion Control Simulation: Adjusts packet sending rate based on network capacity.
Bonus Support: Handles packet reordering with customizable reordering levels.
Requirements
Python 3.x
Mahimahi Network Emulator (optional, for testing packet loss and reordering on Linux)
Setup
Clone this repository:

bash
Copy code
git clone https://github.com/yourusername/custom-transport-protocol.git
cd custom-transport-protocol
Install any additional dependencies (if required).

Download the latest starter code here and replace any previous versions to ensure compatibility.

Usage
Generate a Test File:

Use generate_bogus_text.py to create a test file:
bash
Copy code
python3 generate_bogus_text.py 1000000 > test_file.txt
Start the Receiver:

Run the receiver to listen on a specific IP and port:
bash
Copy code
python3 transport.py --ip localhost --port 7000 receiver
Start the Sender:

Transmit the test file:
bash
Copy code
python3 transport.py --ip localhost --port 7000 --sendfile test_file.txt sender
Testing
Built-in Emulator
Test the protocol’s robustness by simulating different packet loss rates:

bash
Copy code
python3 transport.py --ip localhost --port 7000 --sendfile test_file.txt sender --simloss 0.1
Mahimahi (Optional)
For Linux users, Mahimahi can simulate various network conditions, such as high packet loss or delay. To enable packet loss:

Run Mahimahi’s loss shell:
bash
Copy code
mm-loss uplink 0.1
Start the receiver outside the Mahimahi shell, and run the sender within it, setting the IP to 0.0.0.0.
Packet Reordering (Bonus)
To test packet reordering, add the --pkts_to_reorder option:

bash
Copy code
python3 transport.py --ip localhost --port 7000 --sendfile test_file.txt sender --pkts_to_reorder 5
Notes
UDP is used as the transport layer, but reliability is manually implemented to ensure end-to-end message integrity.
Sequence Numbers: The sender assigns each byte a sequence number for tracking and acknowledgment purposes.
Selective Acknowledgments: Uses JSON-formatted ranges to acknowledge groups of received packets, optimizing communication between sender and receiver.
This repository provides a robust, UDP-based transport protocol that ensures reliable data delivery across unreliable networks, a practical exploration of concepts used in real-world protocols like TCP and QUIC.
