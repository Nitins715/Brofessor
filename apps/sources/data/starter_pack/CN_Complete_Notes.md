# Computer Networks (CN)

> **Source**: [CodeKairo CS Notes](https://codekairo.com/notes/computer-networks)  
> **Overview**: Complete computer networking guide covering OSI vs TCP/IP models, Data Link framing, IP addressing, subnetting, routing algorithms, TCP vs UDP, DNS resolution, HTTP/HTTPS, NAT/DHCP, and network security fundamentals.

---

## Table of Modules

1. [Introduction to Computer Networks](#module-1-introduction-to-computer-networks)
2. [The OSI Model](#module-2-the-osi-model)
3. [The TCP/IP Model](#module-3-the-tcp/ip-model)
4. [Data Link Layer: Framing, Error Control and MAC](#module-4-data-link-layer-framing,-error-control-and-mac)
5. [IP Addressing and Subnetting](#module-5-ip-addressing-and-subnetting)
6. [Routing and Routing Protocols](#module-6-routing-and-routing-protocols)
7. [TCP and UDP](#module-7-tcp-and-udp)
8. [Domain Name System (DNS)](#module-8-domain-name-system-(dns))
9. [HTTP and HTTPS](#module-9-http-and-https)
10. [NAT, DHCP and Ports](#module-10-nat,-dhcp-and-ports)
11. [Network Security Basics](#module-11-network-security-basics)
12. [What Happens When You Type a URL](#module-12-what-happens-when-you-type-a-url)

---

## Module 1: Introduction to Computer Networks

*Original URL: https://codekairo.com/notes/computer-networks/introduction-to-computer-networks*

### Overview

Quick answer

### What is a computer network?

A computer network is a set of devices connected by communication links so they can exchange data and share resources such as files, printers and an internet connection. Networks are classed by the area they cover (PAN, LAN, MAN, WAN), by topology (bus, star, ring, mesh, tree) and by how they move data (circuit or packet switching). The internet is a network of networks.

- What a network is made of
- Types of networks by size
- Network topologies
- Network devices and the layer they work at
- Circuit switching vs packet switching
- Bandwidth, latency and throughput
- Worked example: transmission and propagation delay
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A computer network is two or more devices joined by links so they can exchange data. Networks exist so that resources can be shared (one printer, one internet connection, one database for a whole office), so that people can communicate (email, video calls) and so that a service can keep running when one machine fails. Everything else in this subject, from the OSI model to TCP's handshake, is a detailed answer to one question: how does a stream of bits get from one program to another program on a different machine, correctly and quickly?

### What a network is made of

Every network, from two laptops on a Wi-Fi hotspot to the internet, has the same four ingredients:

- Nodes. End devices (hosts) that create or consume data, such as laptops, phones and servers, and intermediate devices that pass data along, such as switches and routers.
- Links (transmission media). Wired media are twisted-pair copper (Ethernet cables), coaxial cable and optical fibre. Wireless media are radio (Wi-Fi, Bluetooth, cellular), microwave and satellite.
- Protocols. Agreed rules for the format and order of messages and the actions taken on them. IP, TCP and HTTP are protocols. Two devices can only talk if they follow the same ones.
- Services. What the network offers the programs above it: delivering a web page, a file transfer or a DNS lookup.

Links also differ in direction, called the transmission mode :

### Types of networks by size

Networks are named by the area they cover. The distances are typical, not hard limits.

A LAN is usually owned by one organisation and runs at high speed with low delay. A WAN is usually built from links rented from telecom carriers, and it is slower and costlier per bit. The internet is not one network: it is tens of thousands of independently run networks joined by routers and the BGP routing protocol.

### Network topologies

Topology is the layout of the links: who is connected to whom.

The same 5 devices as a bus, a star, a ring and a full mesh. The bus shares one cable, the star gives each device its own link to a switch, the ring passes data one way round, and the mesh links every pair: 10 links for 5 devices.

Full mesh arithmetic. Every pair has its own link, so n devices need n(n − 1)/2 links and n − 1 ports each. Ten devices already need 45 links, which is why full mesh is kept for places where reliability justifies the cost, such as between core routers.

### Network devices and the layer they work at

The layer numbers refer to the OSI model, covered in the next note .

Two clarifications interviewers check. A layer 3 switch also routes between VLANs, so "switch = layer 2" is the textbook default, not a law. And in everyday use, the default gateway on your laptop simply means the router that leads out of your network.

### Hub vs switch vs router: collision and broadcast domains

A collision domain is the part of a network where two simultaneous transmissions collide. A broadcast domain is the set of devices that receive a broadcast frame.

So switches break up collision domains and routers break up broadcast domains.

Each of the switch's 4 ports is its own collision domain, so H1, H2 and H3 never collide. The hub repeats every signal out of every port, so its 4 links are one domain, 5 in all.

- Each of the switch's 4 ports is its own collision domain, so H1, H2 and H3 never collide. The hub repeats every signal out of every port, so its 4 links are one domain, 5 in all.
- A broadcast from H1 is forwarded by the switch to every port but stops at the router, and the hub side is the same: 2 broadcast domains, one per router interface.

### Circuit switching vs packet switching

Circuit switching sets up a dedicated path with reserved capacity before any data flows, keeps it for the whole conversation and then tears it down. The classic telephone network works this way. Packet switching splits data into packets, each carrying the destination address; every router stores a packet, looks at the address and forwards it (store and forward). Packets from many users share every link. The internet works this way. (A third, older scheme, message switching , stores and forwards whole messages.)

The circuit spends 2 units reserving the path, then the bits stream through the switch without stopping and the last arrives at 6. Packets start at once, but the router must hold each whole packet before sending it on; the last arrives at 5.

### Bandwidth, latency and throughput

- Bandwidth is a link's capacity in bits per second (bps). A "100 Mbps" link can carry at most 100 million bits each second.
- Latency is the time a message takes to get from source to destination. The round-trip time (RTT) is the time to go there and back.
- Throughput is the rate actually achieved end to end. It is limited by the slowest link on the path (the bottleneck): a server on a 1 Gbps link sending to a phone on a 20 Mbps connection gets at most 20 Mbps.

The delay a packet sees at each hop has four parts:

Signals travel at about 2 × 10^8 m/s in copper and fibre, roughly two-thirds of the speed of light in a vacuum.

### Worked example: transmission and propagation delay

A host sends one 1,000-byte packet over a single 10 Mbps link that is 2,000 km long. Take the signal speed as 2 × 10^8 m/s and ignore queuing and processing.

Time runs down the page. Pushing 8,000 bits onto a 10 Mbps link takes 0.8 ms, the slab's thickness; each bit then needs 10 ms to cross 2,000 km, its slope. The last bit lands at 10.8 ms.

- Time runs down the page. Pushing 8,000 bits onto a 10 Mbps link takes 0.8 ms, the slab's thickness; each bit then needs 10 ms to cross 2,000 km, its slope. The last bit lands at 10.8 ms.
- Put a router halfway and the propagation adds up to the same 10 ms, but the router must receive all 8,000 bits before it sends the first one on, so the transmission time is paid twice: 11.6 ms.

The bandwidth-delay product is how many bits are "on the wire" at once: 12.5 packets of this size fit in the link before the first one arrives. Protocols that wait for an acknowledgement after every packet waste most of such a link, which is why TCP keeps a window of many packets in flight.

Now send a 1 MB file (8 × 10^6 bits) over the same link. Transmission delay becomes 8 × 10^6 ÷ 10^7 = 0.8 s, while propagation stays 10 ms, so the total is 0.81 s. Small messages are dominated by latency; big transfers are dominated by bandwidth. Doubling the bandwidth would halve the file's time but would not change the 10 ms propagation delay at all.

With a router halfway (two 10 Mbps links of 1,000 km), store and forward pays the transmission delay twice: 2 × 0.8 ms + 2 × 5 ms = 11.6 ms.

### Common mistakes

- Saying a switch sends frames to all ports: it floods only unknown or broadcast destinations; known MAC addresses go to one port.
- Mixing up transmission delay (depends on packet size and bandwidth) with propagation delay (depends on distance and medium).
- Writing that more bandwidth reduces latency for a small packet: it shrinks only the transmission part.
- Calling the internet a WAN owned by someone: it is a network of independently run networks.
- Giving full-mesh links as n(n − 1): each link joins two devices, so divide by 2.
- Placing a router at layer 2 or a hub at layer 2: a hub is layer 1, a router is layer 3.

### Interview questions

What is the difference between a hub and a switch? A hub is a layer 1 device that repeats every signal to every port, so all ports share one collision domain and the bandwidth. A switch is a layer 2 device that learns MAC addresses and forwards each frame only to the destination's port, giving each port its own collision domain and allowing full-duplex links.

How many collision and broadcast domains does a 24-port switch create? Twenty-four collision domains, one per port, and one broadcast domain, because a switch forwards broadcasts out of every port. Configuring VLANs splits the broadcast domain; only a router (or a layer 3 switch) forwards between them.

Why is the star topology preferred over the bus for LANs? In a star, each device has its own cable to the switch, so a faulty cable or device affects only that device and faults are easy to find. In a bus, one break in the shared backbone stops the whole network and every device competes for the same medium.

How many links does a full mesh of n devices need? n(n − 1)/2 links, with n − 1 ports on every device. Six devices need 15 links. The cost grows with the square of n, so full mesh is kept for small sets of critical nodes.

What is the difference between latency and bandwidth? Bandwidth is how many bits per second a link can carry; latency is how long a bit takes to arrive. A satellite link can have high bandwidth and high latency at the same time. For a small request, such as a DNS lookup, latency matters far more than bandwidth.

Does the internet use circuit switching or packet switching, and why? Packet switching. Data traffic is bursty, so sharing links among many users is far more efficient than reserving capacity per conversation, and packets can be rerouted around failures. The price is variable delay and occasional loss, which the transport layer handles.

What is a gateway, and how is it different from a router? A gateway connects networks that use different protocols and translates between them, and it can work at any layer up to the application layer. A router forwards packets between networks that all speak IP. In daily use, "default gateway" just means the router a host sends off-network traffic to.

What is the bandwidth-delay product and why does it matter? It is bandwidth multiplied by the one-way propagation delay: the number of bits in flight on the link. A sender must be allowed at least that much unacknowledged data (TCP's window) to keep the link busy; otherwise it sits idle waiting for acknowledgements.

Next, read the OSI model , and test yourself with the Computer Networks (Basic) skill test .

### What are the four types of computer network by size?

A PAN (personal area network) links devices around one person, such as a phone and earbuds over Bluetooth. A LAN covers a home, office or campus, a MAN covers a city, and a WAN spans countries or continents. The internet is the largest WAN.

### Which network topology is most common today?

The star, in the form of switched Ethernet: every device has its own cable to a central switch. A failed cable affects only one device and devices are easy to add, though the switch itself is a single point of failure. Large networks connect several stars into a tree.

### What is the difference between a hub, a switch and a router?

A hub works at the physical layer and repeats every incoming signal out of every port. A switch works at the data link layer and forwards a frame only to the port where the destination MAC address lives. A router works at the network layer and forwards packets between different networks using IP addresses.

### What is the difference between bandwidth and throughput?

Bandwidth is the maximum rate a link can carry, such as 100 Mbps. Throughput is the rate actually achieved end to end, which is lower because of the slowest link on the path, congestion, protocol overhead and retransmissions.

### Why does the internet use packet switching instead of circuit switching?

Computer traffic comes in bursts, so reserving a circuit for each conversation would leave most of the capacity idle. Packet switching lets many users share each link, and packets can be routed around a failed link. The cost is variable delay and possible loss, which protocols such as TCP handle.


---

## Module 2: The OSI Model

*Original URL: https://codekairo.com/notes/computer-networks/osi-model*

### Overview

Quick answer

### What is the OSI model in computer networks?

The OSI (Open Systems Interconnection) model is a seven-layer reference model, published by ISO in 1984, that divides network communication into the Application, Presentation, Session, Transport, Network, Data Link and Physical layers. Each layer does one job, serves the layer above it and uses the layer below it, so protocols and devices can be designed, described and debugged independently.

- Why networks are layered
- The seven layers at a glance
- What each layer does
- Encapsulation and decapsulation
- A mnemonic for the order
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The OSI model is a way of cutting the job of networking into seven smaller jobs, each handled by one layer. The International Organization for Standardization (ISO) published it in 1984 as the reference model for "open" systems that could talk to each other regardless of vendor. Its own protocols lost to TCP/IP, but its layers became the language every network engineer uses: when someone says a switch is a layer 2 device or a load balancer works at layer 7, they are using OSI numbers.

### Why networks are layered

Sending a web page involves dozens of concerns: turning text into bytes, finding the right program on the server, finding the right machine on the planet, getting a frame across one cable, and turning bits into voltages or light. Layering splits these concerns so that:

- each layer has one job and offers a service to the layer above it through an interface;
- a layer can change without the others noticing (Wi-Fi replaced Ethernet cables without changing HTTP);
- each layer on the sender talks logically to the same layer on the receiver (its peer) by adding a header the peer reads.

The rule to remember: layers 1 to 3 run in every device along the path, while layers 4 to 7 are handled only by the two end hosts .

Data goes down all seven layers of Host A and onto the wire. The switch lifts it only to layer 2 and the router to layer 3; only Host B takes it back up to layer 7, so layers 4 to 7 are a conversation between the two ends.

### The seven layers at a glance

Three kinds of delivery sit at three layers, and interviewers like the distinction:

### Layer 7: Application

The layer closest to the user. It provides network services to applications: fetching web pages (HTTP), sending email (SMTP) and reading it (POP3, IMAP), transferring files (FTP), resolving names (DNS) and remote login (SSH, Telnet). The browser itself is not layer 7; the protocol it speaks is.

### Layer 6: Presentation

Makes sure the receiver can understand the data. Its three classic jobs are translation (between character sets and data formats, such as ASCII and EBCDIC), encryption and decryption , and compression . File formats such as JPEG and MPEG are usually listed here.

### Layer 5: Session

Opens, maintains and closes a dialogue (session) between two applications. It provides dialogue control (who may send, and whether both can send at once) and synchronisation : checkpoints inserted into a long transfer so that, after a failure, it resumes from the last checkpoint instead of from the start. NetBIOS and RPC are the usual examples.

### Layer 4: Transport

Delivers data from a process on one host to a process on another, using port numbers to pick the program (port 443 for HTTPS). It splits a message into segments and reassembles them ( segmentation ), and, in TCP, provides connection setup, end-to-end error control (acknowledgements and retransmission) and flow control (not overrunning the receiver). UDP offers the same port-based delivery without the reliability. See TCP and UDP .

### Layer 3: Network

Moves packets from the source host to the destination host, possibly across many networks. Its jobs are logical addressing (IP addresses), routing (choosing the path) and forwarding, and in IPv4, fragmentation of packets too big for a link. ICMP, used by ping and traceroute , reports errors at this layer.

### Layer 2: Data link

Moves a frame across a single link, from one node to the next. It does framing (marking where a frame starts and ends), physical addressing with MAC addresses, error detection with a CRC in the frame's trailer, flow control between neighbours and medium access control when many devices share a medium. It is split into two sublayers: LLC (logical link control, the interface to layer 3) and MAC (media access control, the interface to layer 1).

### Layer 1: Physical

Transmits raw bits over the medium. It defines connectors and cables, voltage levels or light pulses, how bits are encoded as signals, the bit rate, bit synchronisation, and whether the link is simplex, half-duplex or full-duplex. It does not know what the bits mean.

### Encapsulation and decapsulation

On the way down, each layer takes the unit from the layer above as its payload and adds its own header (the data link layer also adds a trailer , the frame check sequence). This is encapsulation . On the way up at the receiver, each layer reads and removes its own header and passes the payload up. This is decapsulation .

The application layers produce 1,460 bytes of data, here an HTTP request. In TCP/IP the presentation and session jobs happen inside the application, so the data leaves layer 5 as it is.

- The application layers produce 1,460 bytes of data, here an HTTP request. In TCP/IP the presentation and session jobs happen inside the application, so the data leaves layer 5 as it is.
- The transport layer adds a 20-byte TCP header holding the ports, sequence and acknowledgement numbers. Header and payload together are a segment of 1,480 bytes.
- The network layer adds a 20-byte IP header with the source and destination IP addresses, making a 1,500-byte packet: exactly Ethernet's maximum payload, the MTU.
- The data link layer adds a 14-byte Ethernet header with the MAC addresses and a 4-byte trailer, the frame check sequence: a 1,518-byte frame, of which 96.2 per cent is the user's data.
- The physical layer knows nothing of headers: it sends an 8-byte preamble so the receiver can lock on, then the frame's 12,144 bits as signals on the medium.
- At the receiver the data link layer rebuilds the frame, recomputes the check sequence and compares it with the FCS. They match, so it removes its header and trailer and passes the 1,500-byte packet up.
- The network layer reads the destination IP address, sees it is this host's own, and strips the IP header. The protocol field says TCP, so the 1,480-byte segment goes to the transport layer.
- TCP reads the destination port to find the program, checks the sequence number to put the bytes in order, and removes its header.
- The application receives exactly the 1,460 bytes that were sent. Each layer read only its own header, written by its peer on the sender, which is what layering means.

### Worked example: one full-size Ethernet frame

A host sends 1,460 bytes of application data over Ethernet with no IP or TCP options.

So 1,460 of 1,518 bytes, about 96.2 per cent, is the user's data. This is also why the usual TCP maximum segment size on Ethernet is 1,460 bytes: 1,500 − 20 − 20.

### What changes at each hop

A router decapsulates up to layer 3, picks the next hop from the destination IP address and wraps the packet in a new frame for the next link, decrementing the TTL and updating the IP header checksum on the way. So the MAC addresses change at every hop, while the source and destination IP addresses stay the same end to end (unless a NAT device rewrites them, as covered in NAT, DHCP and ports ).

On the first link A addresses the frame to R1's interface m2, from its own m1. The IP header inside names the real destination, B, and starts with TTL 64.

- On the first link A addresses the frame to R1's interface m2, from its own m1. The IP header inside names the real destination, B, and starts with TTL 64.
- R1 strips the frame, reads the destination IP address, decrements the TTL to 63 and builds a new frame for the next link: from m3 to R2's m4. The IP addresses are untouched.
- R2 does the same, so the last frame goes from m5 to B's m6 with TTL 62. The MAC addresses changed on every link; the IP addresses and the destination port stayed the same from end to end.

### Common mistakes

- Calling the transport PDU a packet: it is a segment (TCP) or datagram (UDP); the packet is layer 3.
- Saying MAC addresses travel end to end: they are rewritten at every router; IP addresses are the end-to-end ones.
- Putting the browser or email client at layer 7: the application layer is the protocol (HTTP, SMTP), not the program.
- Listing the layers out of order, especially swapping session and presentation: 5 is session, 6 is presentation.
- Saying the internet runs on OSI: it runs on TCP/IP, and OSI is the reference model used to describe it.
- Forgetting the data link trailer: encapsulation adds headers at every layer, plus the FCS trailer at layer 2.

### Interview questions

Why is network communication divided into layers? Layering breaks a complex problem into smaller jobs with clear interfaces. Each layer can be implemented and replaced independently, as long as it offers the same service to the layer above, and troubleshooting can proceed layer by layer.

What is the difference between the data link layer and the network layer? The data link layer delivers frames across one link between neighbouring nodes using MAC addresses. The network layer delivers packets from the source host to the destination host across many links, using IP addresses and routing.

Which layer does a switch work at, and which does a router? A switch works at layer 2: it forwards frames using MAC addresses. A router works at layer 3: it forwards packets between networks using IP addresses. Layer 3 switches combine both.

Which OSI layer uses port numbers, and why are they needed? The transport layer. An IP address only identifies a host; the port number identifies the process on that host, so a server can run a web server on port 443 and an SSH server on port 22 at the same address.

What happens to the IP and MAC addresses as a packet crosses three routers? The source and destination IP addresses stay the same all the way (barring NAT). The MAC addresses are replaced at every hop, because each router builds a new frame addressed to the next device on the next link.

What does the session layer do? Give an example. It sets up, manages and ends sessions between applications, controls whose turn it is to send and adds checkpoints so a long transfer can resume after a failure. RPC and NetBIOS sessions are textbook examples; in TCP/IP these duties live inside applications.

Name the two sublayers of the data link layer. LLC (logical link control), which interfaces with the network layer and can provide flow and error control, and MAC (media access control), which handles addressing and decides who may use a shared medium, for example with CSMA/CD.

Where does TLS fit in the OSI model? It does not map cleanly. It runs on top of TCP and below HTTP, and its jobs (encryption, authentication) are presentation-layer jobs in the textbook, so it is usually taught at layer 6, sometimes at layer 5 or 4. Say that it sits between the transport and application layers.

Next, read the TCP/IP model , and test yourself with the Computer Networks (Basic) skill test .

### What are the 7 layers of the OSI model in order?

From top to bottom: Application (7), Presentation (6), Session (5), Transport (4), Network (3), Data Link (2) and Physical (1). A common mnemonic from the top is "All People Seem To Need Data Processing", and from the bottom "Please Do Not Throw Sausage Pizza Away".

### What is a PDU in the OSI model?

A protocol data unit is the name of the chunk of data at a given layer, including that layer's header. The transport layer's PDU is a segment (a datagram for UDP), the network layer's is a packet, the data link layer's is a frame, and the physical layer carries bits.

### At which OSI layer does a router work?

A router works at layer 3, the network layer. It reads the destination IP address in each packet, looks it up in its routing table and forwards the packet towards the destination network. Switches work at layer 2 and hubs at layer 1.

### Is the OSI model used in real networks?

Not as a protocol suite. The internet runs on the TCP/IP model, and the OSI protocols themselves never caught on. The OSI model survives as the shared vocabulary for teaching and troubleshooting, which is why engineers say "a layer 2 problem" or "a layer 7 load balancer".

### Which OSI layer handles encryption?

In the textbook model, encryption, compression and data translation belong to the presentation layer (layer 6). Real protocols do not line up neatly: TLS sits between TCP and the application, and IPsec encrypts at the network layer.


---

## Module 3: The TCP/IP Model

*Original URL: https://codekairo.com/notes/computer-networks/tcp-ip-model*

### Overview

Quick answer

### What is the TCP/IP model?

The TCP/IP model, also called the Internet protocol suite, is the layered architecture the internet actually runs on. RFC 1122 describes four layers: Application, Transport, Internet and Link (network access). It is named after its two core protocols, TCP and IP. Many textbooks teach a five-layer version that splits the link layer into data link and physical.

- The four layers
- How TCP/IP maps to OSI
- Worked example: how each layer knows what is inside
- Where the tricky protocols sit
- OSI vs TCP/IP
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The TCP/IP model describes the protocol suite that runs the internet. It grew out of ARPANET research funded by the US Department of Defense, which is why older books call it the DoD model, and ARPANET switched over to TCP/IP on 1 January 1983. Unlike OSI, which was designed on paper first, TCP/IP was written down after the protocols already worked: RFC 1122 (1989) describes the layers that hosts implement. Interviewers ask about it mostly in comparison with the OSI model , so this note keeps both in view.

### Application layer

Everything an application needs from the network lives here: the protocol's message format (an HTTP request, a DNS query), and any encryption, compression or session handling, which OSI would put in layers 5 and 6. TLS sits between this layer and TCP, and HTTPS is simply HTTP carried inside TLS.

### Transport layer

TCP gives a reliable, ordered, connection-oriented byte stream with flow control and congestion control. UDP gives connectionless, best-effort datagrams with almost no overhead. Both use 16-bit port numbers to deliver data to the right program. QUIC, which HTTP/3 uses, builds reliability on top of UDP. The details are in TCP and UDP .

### Internet layer

IP gives every interface an address and moves packets hop by hop towards the destination network. IP is connectionless and best effort : it does not promise delivery, order or freedom from duplicates; those are left to the transport layer. ICMP carries IP's error and diagnostic messages, such as "destination unreachable" and the echo request and reply that ping uses.

### Link layer

The link (or network access) layer moves a frame across one physical network to the next hop, using hardware addresses (MAC addresses on Ethernet and Wi-Fi). TCP/IP deliberately says little about it: IP runs over whatever link exists. ARP, which finds the MAC address for an IP address on the local network, is usually placed here.

### How TCP/IP maps to OSI

Many Indian university syllabi and popular textbooks teach a five-layer hybrid, because it keeps the useful split between framing and signalling. If an interviewer asks "how many layers?", answer "four in the RFC, five in the textbook hybrid" and name them.

Each box spans the OSI layers it does the job of. TCP/IP's application layer absorbs OSI's top three and its link layer the bottom two; the textbook's five-layer model keeps data link and physical apart.

### Worked example: how each layer knows what is inside

A receiving host has to hand each unit to the right protocol above it. Every header carries a field that names its payload, so the host can demultiplex a frame step by step.

A browser's request, 37 bytes of text, wrapped three times: a 20-byte TCP header makes a 57-byte segment, a 20-byte IP header a 77-byte packet, and Ethernet's 14-byte header and 4-byte FCS a 95-byte frame.

- A browser's request, 37 bytes of text, wrapped three times: a 20-byte TCP header makes a 57-byte segment, a 20-byte IP header a 77-byte packet, and Ethernet's 14-byte header and 4-byte FCS a 95-byte frame.
- The link layer checks the FCS and reads the EtherType, 0x0800: the payload is an IPv4 packet, so it strips the header and trailer and hands the 77 bytes to IP.
- IP sees its own address as the destination and reads the Protocol field, 6: the payload is a TCP segment, so the 57 bytes go to TCP.
- TCP reads the destination port, 80, and finds the socket of the process listening there, the web server.
- The server reads the 37-byte request. Three header fields, one per layer, named what each payload was; 58 of the frame's 95 bytes were headers and trailer.

In IPv6 the Protocol field's job is done by the Next Header field.

### Where the tricky protocols sit

Some protocols do a lower layer's job but are carried as application data. Interviewers use them to check that you know the difference between a protocol's purpose and its position.

Each line joins a protocol to the one that carries it, labelled with the port, protocol number or EtherType that names it there. All 6 application protocols reach the wire through IP, which runs over any link; ICMP and OSPF ride inside IP yet belong to the internet layer.

### OSI vs TCP/IP

The two service rows follow Tanenbaum's comparison and are a frequent written-exam question: OSI offers both kinds of service at the network layer but only connection-oriented service at the transport layer; TCP/IP is the other way round.

### Common mistakes

- Saying TCP/IP has exactly five layers without qualification: the RFC model has four; five is the textbook hybrid.
- Calling the TCP/IP internet layer "the network layer of TCP/IP" and then putting ARP in it: ARP is usually a link-layer protocol.
- Forgetting that session and presentation duties still exist in TCP/IP: they are done by the application or by TLS.
- Saying IP is reliable: IP is best effort; reliability comes from TCP or from the application.
- Classifying RIP and BGP by purpose rather than position: both are routing protocols carried as application data (UDP and TCP).
- Thinking HTTP/3 means "no transport layer": it runs over QUIC, which runs over UDP.

### Interview questions

What are the layers of the TCP/IP model and what does each do? Application (protocols programs use, such as HTTP and DNS), Transport (process-to-process delivery with TCP or UDP), Internet (addressing and routing packets with IP) and Link (moving frames across the local network, such as Ethernet or Wi-Fi). Mention the five-layer variant if the interviewer seems to expect it.

How is the TCP/IP model different from the OSI model? TCP/IP has four layers and was written to describe working protocols; OSI has seven and was designed before its protocols. TCP/IP merges session and presentation into the application layer, offers only connectionless service at the internet layer and both kinds at the transport layer, and is the model the internet actually uses.

Why did TCP/IP win over the OSI protocols? It was already running on ARPANET and was freely included in widely used operating systems such as BSD Unix, while the OSI protocols arrived later and were complex to implement. A working, free, good-enough implementation won adoption first.

Is IP connection-oriented? What does "best effort" mean? No. IP is connectionless: every packet is routed independently with no setup. Best effort means IP tries to deliver each packet but promises nothing about delivery, order, delay or duplication; TCP adds those guarantees where an application needs them.

At which layer does ICMP work, given that it is carried inside IP? At the internet layer. ICMP messages are encapsulated in IP packets (protocol number 1), but ICMP exists only to serve IP, reporting errors such as unreachable destinations and expired TTLs, so it is treated as part of the internet layer.

How does a host know which protocol to hand a received packet to? Each header names its payload: Ethernet's EtherType (0x0800 for IPv4), IP's Protocol field (6 for TCP, 17 for UDP) and the transport header's destination port (443 for HTTPS). The host demultiplexes upwards using these fields.

Where does DNS sit, and which transport does it use? DNS is an application-layer protocol. It normally uses UDP port 53 for queries, and TCP port 53 for zone transfers and for answers too large for UDP. See DNS .

Next, read IP addressing and subnetting , and test yourself with the Computer Networks (Basic) skill test .

### How many layers does the TCP/IP model have?

Four in the original definition (RFC 1122): Application, Transport, Internet and Link. Textbooks such as Forouzan's and Kurose and Ross's use five layers, splitting Link into Data Link and Physical. Both are correct if you say which version you mean.

### How does the TCP/IP model map to the OSI model?

OSI's application, presentation and session layers merge into the TCP/IP application layer. Transport maps to transport, and the OSI network layer maps to the internet layer. The OSI data link and physical layers together form the TCP/IP link (network access) layer.

### What is the main difference between the OSI and TCP/IP models?

OSI is a seven-layer reference model designed before its protocols, used today for teaching and troubleshooting. TCP/IP is a four-layer model written to describe protocols that already worked, and it is what the internet runs on. TCP/IP folds session and presentation duties into the application.

### Which protocols work at the internet layer of the TCP/IP model?

IP (IPv4 and IPv6) is the core protocol, with ICMP for error reporting and diagnostics (ping), IGMP for IPv4 multicast group membership and IPsec for security. OSPF is also carried directly in IP. ARP is usually placed in the link layer because it never leaves the local network.

### Why is it called the TCP/IP model?

It is named after its two most important protocols: the Transmission Control Protocol, which provides reliable byte streams between programs, and the Internet Protocol, which addresses and routes packets between networks. The suite also includes UDP, ICMP, DNS, HTTP and many others.


---

## Module 4: Data Link Layer: Framing, Error Control and MAC

*Original URL: https://codekairo.com/notes/computer-networks/data-link-layer*

### Overview

Quick answer

### What does the data link layer do in computer networks?

The data link layer (layer 2) moves frames between two directly connected nodes. It packs packets into frames, adds source and destination MAC addresses, detects transmission errors with a CRC in the frame's trailer, can control the flow between sender and receiver, and decides which device may transmit on a shared medium. Ethernet, Wi-Fi and PPP are data link protocols, and switches work at this layer.

- What the data link layer does
- Framing
- Error detection
- Error correction: Hamming code
- Flow control: stop-and-wait and sliding windows
- MAC addresses and ARP
- The Ethernet frame
- Medium access: CSMA/CD vs CSMA/CA
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The physical layer moves raw bits, and bits get corrupted, collide and arrive faster than a receiver can handle. The data link layer turns that unreliable bit pipe into a service the network layer can use: frames with clear boundaries, addressed to a neighbour, checked for errors and sent only when the medium is free. Its scope is a single link, from one node to the next; the network layer strings links together into paths. This note covers each of its jobs with worked examples.

### What the data link layer does

- Framing : marking where each frame starts and ends.
- Physical addressing : source and destination MAC addresses in every frame.
- Error control : detecting damaged frames (CRC), and on some links retransmitting them.
- Flow control : not sending faster than the receiver can accept.
- Medium access control : deciding who transmits when many devices share a medium.

IEEE splits the layer into an upper LLC (logical link control) sublayer, which faces the network layer, and a lower MAC (media access control) sublayer, which handles addressing and medium access.

### Framing

The receiver sees a stream of bits and must find frame boundaries. Four methods:

Byte stuffing: a FLAG byte marks each end of the frame, so a FLAG or ESC inside the data gets an ESC in front of it. A FLAG B ESC C goes out as A ESC FLAG B ESC ESC C, and the receiver drops each ESC and keeps the byte after it.

- Byte stuffing: a FLAG byte marks each end of the frame, so a FLAG or ESC inside the data gets an ESC in front of it. A FLAG B ESC C goes out as A ESC FLAG B ESC ESC C, and the receiver drops each ESC and keeps the byte after it.
- Bit stuffing: the flag is 01111110, six 1s in a row. After any five 1s the sender inserts a 0, so 011111110 goes out as 0111110110 with the stuffed bit at position 7. The receiver deletes the 0 after any five 1s.

PPP uses byte stuffing; HDLC uses bit stuffing. Either way the receiver undoes the rule, so the data can never be mistaken for a boundary.

### Parity

A parity bit makes the count of 1s even (even parity) or odd. The data 1011001 has four 1s, so its even parity bit is 0 and 10110010 is sent. Single parity detects any odd number of flipped bits but misses any even number. Two-dimensional parity arranges data in a grid with a parity bit per row and column; it can detect all 1-, 2- and 3-bit errors and can locate and correct a single-bit error.

### Checksum

The sender adds the data words in one's complement arithmetic (a carry out of the top is wrapped round and added back) and sends the complement of the sum. Take 4-bit words 7, 11, 12, 0 and 6:

The Internet checksum used by IP, TCP and UDP is the same idea with 16-bit words. It is cheap but weak: swapping two words leaves the sum unchanged.

### Cyclic redundancy check (CRC)

CRC treats bits as polynomial coefficients (1011 is x^3 + x + 1) and uses modulo-2 division , where subtraction is XOR and there are no carries. With a generator of degree r (r + 1 bits):

- Append r zeros to the data.
- Divide by the generator using XOR; the remainder has r bits.
- Replace the appended zeros with the remainder and send this codeword .
- The receiver divides the codeword by the same generator; a remainder of zero means no error was detected.

Worked example. Data 11010110, generator 1011 (degree 3), so three zeros are appended.

The generator 1011 has degree 3, so 3 zeros are appended to the data 11010110. The division runs on these 11 bits, and subtraction is XOR: no carries, no borrows.

- The generator 1011 has degree 3, so 3 zeros are appended to the data 11010110. The division runs on these 11 bits, and subtraction is XOR: no carries, no borrows.
- Step 1: the leading bit is 1, so XOR the generator under it: 1101 ⊕ 1011 = 0110. The leading bit becomes 0 and the window moves one bit right.
- Step 2: the leading bit is 1, so XOR the generator under it: 1100 ⊕ 1011 = 0111. The leading bit becomes 0 and the window moves one bit right.
- Step 3: the leading bit is 1, so XOR the generator under it: 1111 ⊕ 1011 = 0100. The leading bit becomes 0 and the window moves one bit right.
- Step 4: the leading bit is 1, so XOR the generator under it: 1001 ⊕ 1011 = 0010. The leading bit becomes 0 and the window moves one bit right.
- Step 5: the leading bit is 0, so XOR 0000 — 0100 stays 0100. A zero leading bit means the generator does not go in here; the window just moves on.
- Step 6: the leading bit is 1, so XOR the generator under it: 1000 ⊕ 1011 = 0011. The leading bit becomes 0 and the window moves one bit right.
- Step 7: the leading bit is 0, so XOR 0000 — 0110 stays 0110. A zero leading bit means the generator does not go in here; the window just moves on.
- Step 8: the leading bit is 1, so XOR the generator under it: 1100 ⊕ 1011 = 0111. The leading bit becomes 0 and the window moves one bit right.
- After 8 steps only the last 3 bits can be non-zero: the remainder is 111. It replaces the appended zeros, and 11010110111 is the codeword that goes on the wire.
- The receiver divides what arrives by 1011. The codeword leaves 000, so it is accepted; with the fourth bit flipped in transit it leaves 001, not zero, and the frame is discarded.

The remainder is 111 , so the codeword is 11010110111 . Dividing 11010110111 by 1011 leaves 000, so the receiver accepts it. If the fourth bit flips in transit (11000110111), the remainder is 001, not zero, and the error is detected. The program below runs the same division.

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
string
remainderOf
(
string work
,
const
string
&
generator
)
{
size_t n
=
generator
.
size
(
)
-
1
;
for
(
size_t i
=
0
;
i
+
n
<
work
.
size
(
)
;
i
++
)
{
if
(
work
[
i
]
==
'1'
)
{
for
(
size_t j
=
0
;
j
<
generator
.
size
(
)
;
j
++
)
work
[
i
+
j
]
=
work
[
i
+
j
]
==
generator
[
j
]
?
'0'
:
'1'
;
}
}
return
work
.
substr
(
work
.
size
(
)
-
n
)
;
}
int
main
(
)
{
string data
=
"11010110"
,
generator
=
"1011"
;
string remainder
=
remainderOf
(
data
+
string
(
generator
.
size
(
)
-
1
,
'0'
)
,
generator
)
;
string codeword
=
data
+
remainder
;
string corrupted
=
codeword
;
corrupted
[
3
]
=
corrupted
[
3
]
==
'0'
?
'1'
:
'0'
;
cout
<<
"data       "
<<
data
<<
"\n"
;
cout
<<
"generator  "
<<
generator
<<
"\n"
;
cout
<<
"remainder  "
<<
remainder
<<
"\n"
;
cout
<<
"codeword   "
<<
codeword
<<
"\n"
;
cout
<<
"check      "
<<
remainderOf
(
codeword
,
generator
)
<<
"\n"
;
cout
<<
"corrupted  "
<<
corrupted
<<
" -> "
<<
remainderOf
(
corrupted
,
generator
)
<<
"\n"
;
return
0
;
}
```

Output

```
data       11010110
generator  1011
remainder  111
codeword   11010110111
check      000
corrupted  11000110111 -> 001
```

A generator of degree r with a non-zero constant term detects every burst error of length r or less, and one with x + 1 as a factor detects every odd number of bit errors. Longer bursts slip through only with probability about 2^−r, which is why Ethernet's 32-bit CRC is so strong.

### Error correction: Hamming code

To correct one bit among m data bits, r check bits are needed with 2^r ≥ m + r + 1 . For m = 4 that gives r = 3, the Hamming(7,4) code. Check bits sit at the positions that are powers of 2 (1, 2, 4); check bit p covers every position whose binary number has that bit set.

Encode 1011 with even parity, then correct an error.

The data bits 1011 go into positions 3, 5, 6, 7; positions 1, 2 and 4, the powers of 2, are check bits. Check bit c covers every position whose binary number has c's bit set, so the groups overlap.

- The data bits 1011 go into positions 3, 5, 6, 7; positions 1, 2 and 4, the powers of 2, are check bits. Check bit c covers every position whose binary number has c's bit set, so the groups overlap.
- Group 1 covers positions 1, 3, 5, 7. Positions 3, 5, 7 hold 1, 0, 1: 2 ones, so even parity makes p1 = 0.
- Group 2 covers positions 2, 3, 6, 7. Positions 3, 6, 7 hold 1, 1, 1: 3 ones, so even parity makes p2 = 1.
- Group 4 covers positions 4, 5, 6, 7. Positions 5, 6, 7 hold 0, 1, 1: 2 ones, so even parity makes p4 = 0.
- 0110001 arrives instead of 0110011. The receiver rechecks every group: group 1 still has even parity, but groups 2 and 4 now have odd parity, so c1 = 0, c2 = 1 and c4 = 1.
- Read the checks as a binary number, c4 c2 c1 = 110 = 6: position 6 is the only one inside both failing groups and outside the passing one. Flipping it back restores 0110011.

The codeword is 0110011 . If 0110001 arrives instead, the rechecks give c1 = 0, c2 = 1 and c4 = 1, and c4 c2 c1 = 110 = 6 is the position to flip back. Hamming(7,4) has a minimum distance of 3, so it corrects one error or detects two (detecting d errors needs distance d + 1; correcting t needs 2t + 1).

### Flow control: stop-and-wait and sliding windows

With stop-and-wait , the sender sends one frame and waits for its acknowledgement (ARQ, automatic repeat request, resends on timeout). With transmission time Tt and propagation delay Tp, its efficiency is Tt / (Tt + 2Tp) = 1 / (1 + 2a), where a = Tp / Tt.

Worked example. 1,000-bit frames on a 1 Mbps link give Tt = 1 ms; with Tp = 10 ms, a = 10 and efficiency = 1 / 21, about 4.8 per cent. A sliding window of N frames gives N / (1 + 2a), so 21 frames in flight keep the link fully busy. With m-bit sequence numbers, Go-Back-N allows a window of at most 2^m − 1, so it needs m = 5 (window up to 31); Selective Repeat allows at most 2^(m−1), so it needs m = 6 (window up to 32).

Go-Back-N: the receiver accepts only the frame it expects next, so it discards 3, 4, 5 and 6 even though they arrived intact. When frame 2's timer runs out the sender goes back and resends 2, 3, 4, 5, 6: 12 transmissions for 7 frames.

- Go-Back-N: the receiver accepts only the frame it expects next, so it discards 3, 4, 5 and 6 even though they arrived intact. When frame 2's timer runs out the sender goes back and resends 2, 3, 4, 5, 6: 12 transmissions for 7 frames.
- Selective Repeat: the receiver buffers 3 to 6 and acknowledges each one, so the sender resends only frame 2. When it arrives, frames 2 to 6 go up to the network layer in order: 8 transmissions in all.

Stop-and-wait needs just 1-bit sequence numbers (0 and 1), so it is also called the alternating bit protocol.

### MAC addresses and ARP

A MAC address is 48 bits, written as six hexadecimal bytes such as 00:1A:2B:3C:4D:5E. The first three bytes are the manufacturer's OUI (organisationally unique identifier). FF:FF:FF:FF:FF:FF is the broadcast address. MAC addresses are flat and identify an interface on its local link; IP addresses are hierarchical and identify where it sits in the internet.

ARP maps an IPv4 address to a MAC address on the local network. When 192.168.1.10 wants to send to 192.168.1.20:

- It checks its ARP cache; on a miss it broadcasts a request to FF:FF:FF:FF:FF:FF: "Who has 192.168.1.20? Tell 192.168.1.10", including its own MAC address.
- Only 192.168.1.20 replies, with a unicast frame carrying its MAC address.
- The sender caches the answer for a few minutes and sends its frame.

If the destination is on another network (say 8.8.8.8), the host never ARPs for it: it ARPs for its default gateway and sends the frame to the router's MAC address, with the IP packet still addressed to 8.8.8.8. A gratuitous ARP announces a host's own mapping, to detect duplicate addresses or update caches after a failover.

### The Ethernet frame

Counting from the destination address to the FCS, a frame is 6 + 6 + 2 + 46 + 4 = 64 bytes at least and 6 + 6 + 2 + 1,500 + 4 = 1,518 at most. The preamble and SFD only synchronise the receiver and are not counted.

The preamble and start frame delimiter (SFD) only synchronise the receiver. EtherType names the payload (0x0800 IPv4, 0x86DD IPv6, 0x0806 ARP), and a frame runs from 64 to 1,518 bytes ; a payload shorter than 46 bytes is padded.

### Medium access: CSMA/CD vs CSMA/CA

CSMA/CD (carrier sense multiple access with collision detection) was classic half-duplex Ethernet's method: listen until the cable is idle, transmit while listening, and on a collision stop, send a jam signal and back off. After the n-th collision, a station waits K slot times (512 bit times), with K picked at random from 0 to 2^min(n, 10) − 1, and it gives up after 16 attempts. A sender must still be transmitting when news of a collision returns, so Tt ≥ 2Tp and the minimum frame is L = 2 × Tp × R: with Tp = 25.6 µs at 10 Mbps, L = 512 bits = 64 bytes.

A senses an idle cable and starts sending at time 0. Its signal needs the propagation delay Tp = 25.6 µs to reach B at the far end of the longest cable allowed.

- A senses an idle cable and starts sending at time 0. Its signal needs the propagation delay Tp = 25.6 µs to reach B at the far end of the longest cable allowed.
- Just before A's signal arrives, B still hears silence and starts sending too. The two signals collide next to B at once, but A cannot know until the collision's signal travels all the way back.
- The news reaches A at 2 × Tp = 51.2 µs. A detects the collision only if it is still transmitting then, so a frame must last at least 2 × Tp × R = 512 bit times: 64 bytes at 10 Mbps.

Full-duplex switched Ethernet has no collisions, so CSMA/CD is unused there.

CSMA/CA (collision avoidance) is Wi-Fi's method. A radio cannot hear others while transmitting, and two stations may each hear the access point but not each other (the hidden terminal problem), so collisions cannot be detected. A station waits for the medium to be idle for a gap called DIFS plus a random backoff, then sends; the receiver acknowledges after a shorter gap (SIFS). No acknowledgement means a collision, so the station doubles its backoff range and retries. An optional RTS/CTS exchange reserves the medium first.

### Common mistakes

- In CRC, forgetting to append r zeros (r = generator bits − 1), or subtracting with borrows instead of XOR.
- Saying parity detects all errors: it misses every even number of flipped bits.
- Giving Go-Back-N and Selective Repeat the same window limit: 2^m − 1 versus 2^(m−1).
- ARPing for a remote host's IP address: the host resolves its gateway's MAC address.
- Counting the preamble in Ethernet's 64-byte minimum frame.
- Saying Wi-Fi uses CSMA/CD.

### Interview questions

Why does the receiver get a zero remainder when it divides a CRC codeword? The sender appended the remainder of dividing the shifted data by the generator. In modulo-2 arithmetic adding and subtracting are both XOR, so the codeword equals the shifted data minus its remainder, an exact multiple of the generator. Any error that is not itself a multiple of the generator leaves a non-zero remainder.

How many check bits does a Hamming code need for 7 data bits? Four, because the smallest r with 2^r ≥ 7 + r + 1 is 4 (16 ≥ 12, while 8 is less than 11). The code is Hamming(11,7), with check bits at positions 1, 2, 4 and 8.

Why must Selective Repeat's window be at most half the sequence space? If the window were larger, after a batch of lost acknowledgements the receiver could not tell retransmitted old frames from new frames that reuse the same sequence numbers. Keeping the window at 2^(m−1) makes the old and new windows never overlap.

What is the minimum frame size in Ethernet, and why? 64 bytes, from destination address to FCS. With CSMA/CD a station must still be transmitting when a collision from the far end of the longest allowed cable comes back, so a frame must last at least one round-trip time: 512 bit times at 10 Mbps.

What does a switch do with a frame for an unknown MAC address? It floods the frame out of every port except the one it arrived on. It learns addresses by recording the source MAC address of every frame against its incoming port, so once the destination replies, later frames go only to the right port.

Why can't Wi-Fi use collision detection? A transmitting radio's own signal drowns out anything it might hear, and with hidden terminals the colliding station may be out of range entirely. So Wi-Fi avoids collisions with waiting gaps, random backoff and optional RTS/CTS, and uses acknowledgements to discover failures.

Next, read NAT, DHCP and ports , and test the arithmetic with the Computer Networks (Intermediate) skill test .

### What is the difference between error detection and error correction?

Error detection only tells the receiver that a frame was damaged, using parity, a checksum or a CRC; the frame is then discarded or retransmitted. Error correction adds enough redundancy, as in Hamming codes, for the receiver to work out which bits are wrong and fix them without a retransmission.

### What is CRC and how does it work?

A cyclic redundancy check treats the data bits as a polynomial and divides it, using modulo-2 arithmetic, by an agreed generator polynomial. The sender appends the remainder to the data; the receiver divides the whole frame by the same generator, and any non-zero remainder means the frame was corrupted. Ethernet uses a 32-bit CRC.

### What is the difference between Go-Back-N and Selective Repeat?

Both keep a window of unacknowledged frames in flight. In Go-Back-N the receiver accepts frames only in order, so after a loss the sender resends the lost frame and every frame after it. In Selective Repeat the receiver buffers out-of-order frames and the sender resends only the frames actually lost.

### What is ARP in networking?

The Address Resolution Protocol finds the MAC address that belongs to an IPv4 address on the local network. A host broadcasts "who has this IP address?", the owner replies with its MAC address, and the answer is cached. For a destination on another network, the host resolves its default gateway's MAC address instead.

### What is the difference between CSMA/CD and CSMA/CA?

CSMA/CD, used by classic half-duplex Ethernet, transmits after sensing an idle medium, detects collisions while sending, and backs off and retries. CSMA/CA, used by Wi-Fi, cannot detect collisions, so it tries to avoid them with waiting gaps and random backoff before sending, and treats a missing acknowledgement as a collision.

### What is bit stuffing?

Bit stuffing keeps a frame's data from imitating the flag pattern 01111110 that marks frame boundaries in HDLC-style protocols. Whenever the sender sees five consecutive 1s in the data, it inserts a 0; the receiver removes any 0 that follows five 1s. So 01111111 is sent as 011111011.


---

## Module 5: IP Addressing and Subnetting

*Original URL: https://codekairo.com/notes/computer-networks/ip-addressing-and-subnetting*

### Overview

Quick answer

### What is subnetting in computer networks?

Subnetting divides one IP network into smaller networks, called subnets, by borrowing host bits for the network part of the address. A subnet mask or CIDR prefix such as /26 says how many leading bits identify the network; the remaining h bits identify hosts. Each subnet has 2^h addresses and 2^h − 2 usable hosts, because the first is the network address and the last is the broadcast address.

- IPv4 address structure
- Classful addressing: classes A to E
- Special and private addresses
- Subnet masks and CIDR
- Worked example: four subnets from 192.168.10.0/24
- VLSM: subnets of different sizes
- Supernetting (route aggregation)
- IPv4 vs IPv6
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Every device on an IP network needs an address so packets can find it, and every router needs a way to tell which addresses live behind which link. An IPv4 address answers both: its leading bits name a network and its trailing bits name a host on that network. Subnetting is the skill of moving that boundary to cut one block of addresses into smaller networks, and it is the arithmetic most often asked on paper in networking interviews. This note works every number out; check them yourself as you read.

### IPv4 address structure

An IPv4 address is 32 bits , written as four 8-bit octets in decimal separated by dots: 192.168.10.150. Each octet is 0 to 255. There are 2^32 = 4,294,967,296 possible addresses.

Converting an octet to binary uses the place values 128, 64, 32, 16, 8, 4, 2, 1:

An address has two parts: the network portion (identical for every host on that network) and the host portion (unique per host). Where the split falls is given by the subnet mask.

### Classful addressing: classes A to E

Before 1993, the first bits of an address fixed its class and therefore its network/host split.

A class is fixed by the first bits of the first octet: a leading 0 is class A, half of all addresses (0 to 127); 10 is B and 110 is C, each half of what is left. D (1110) is multicast and E (1111) reserved, with no default mask.

In class A, network 0 and network 127 are reserved, which is why only 126 class A networks are usable. Classes wasted addresses badly: an organisation needing 300 hosts was too big for a class C and got a class B with 65,534 host addresses. That waste is why CIDR replaced classes.

### Special and private addresses

Private addresses (RFC 1918) can be reused by any organisation because they are never routed on the public internet; a router doing NAT translates them to a public address on the way out.

### Subnet masks and CIDR

A subnet mask is 32 bits with 1s for the network part and 0s for the host part. CIDR (Classless Inter-Domain Routing, 1993) writes the number of 1s as a prefix length: 255.255.255.192 is /26 because 11111111.11111111.11111111.11000000 has 26 ones. With h = 32 − prefix host bits:

- addresses per subnet = 2^h, usable hosts = 2^h − 2;
- borrowing s bits from the host part creates 2^s subnets;
- block size = 256 − (mask value in the octet where the boundary falls). Subnets start at multiples of it.

### Worked example: four subnets from 192.168.10.0/24

Task. Split 192.168.10.0/24 into four equal subnets and give each one's network address, host range and broadcast address.

- Subnets needed: 4. Borrow s bits so that 2^s ≥ 4, so s = 2.
- New prefix: 24 + 2 = /26. Mask: the last octet is 11000000 = 192, so 255.255.255.192.
- Host bits: h = 32 − 26 = 6. Addresses per subnet 2^6 = 64; usable hosts 64 − 2 = 62.
- Block size: 256 − 192 = 64, so the subnets start at .0, .64, .128 and .192.

Check: each broadcast is one less than the next network address, and 4 × 64 = 256 covers the whole /24.

Four subnets need 2 borrowed bits, since 2^2 = 4, so the prefix grows from /24 to /26. That leaves 6 host bits: each subnet is a block of 64 addresses.

- Four subnets need 2 borrowed bits, since 2^2 = 4, so the prefix grows from /24 to /26. That leaves 6 host bits: each subnet is a block of 64 addresses.
- Subnet bits 00: with the host bits all 0 the last octet is 0, the network address; all 1 gives 63, the broadcast. Everything between is a host.
- Subnet bits 01: the network is .64 and the broadcast .127, so this block starts exactly where the last one ended.
- Subnet bits 10: the network is .128 and the broadcast .191, so this block starts exactly where the last one ended.
- Subnet bits 11: the network is .192 and the broadcast .255, so this block starts exactly where the last one ended. The four blocks fill the /24: 4 × 64 = 256.

### Which subnet does 192.168.10.150/26 belong to?

AND the address with the mask to get the network address; set every host bit to 1 to get the broadcast.

Every IPv4 address is 32 bits, four octets of eight. The last octet here is 150 = 10010110 in binary; the first three are 192, 168 and 10.

- Every IPv4 address is 32 bits, four octets of eight. The last octet here is 150 = 10010110 in binary; the first three are 192, 168 and 10.
- /26 means the mask is 26 ones and then 6 zeros, 255.255.255.192. Bits left of the line name the network; the 6 to its right name a host on it.
- AND each bit with the mask: the network bits pass through and the host bits become 0. The last octet 10010110 becomes 10000000, so the network address is 192.168.10.128.
- Set every host bit to 1 instead and you get the broadcast address, 192.168.10.191. The 6 host bits give 2^6 = 64 addresses; less these two, 62 hosts, .129 to .190.

On paper, only the last octet changes:

So the host is in subnet 3: hosts .129 to .190, broadcast .191. The shortcut gives the same answer: 150 lies between the block starts 128 and 192, so the network is .128.

### A prefix off the octet boundary: 172.16.45.200/20

- /20 means the boundary falls inside the third octet: 20 = 8 + 8 + 4, so the third octet of the mask is 11110000 = 240. Mask: 255.255.240.0.
- Block size in the third octet: 256 − 240 = 16. Blocks start at 0, 16, 32, 48 …
- The third octet 45 lies in the block 32 to 47 (in binary, 00101101 AND 11110000 = 00100000 = 32).
- Network 172.16.32.0, broadcast 172.16.47.255 (third octet 47, fourth octet all 1s).
- First host 172.16.32.1, last host 172.16.47.254, usable hosts 2^12 − 2 = 4,094.

### The same calculation as a program

The program converts the address to a 32-bit number, builds the mask from the prefix, and gets the network with AND and the broadcast with OR of the inverted mask.

```
#
include
<cstdint>
#
include
<cstdio>
#
include
<string>
uint64_t
toInt
(
const
std
::
string
&
ip
)
{
uint64_t
n
=
0
,
part
=
0
;
for
(
char
c
:
ip
+
"."
)
{
if
(
c
==
'.'
)
{
n
=
(
n
<<
8
)
|
part
;
part
=
0
;
}
else
part
=
part
*
10
+
(
c
-
'0'
)
;
}
return
n
;
}
std
::
string
toIp
(
uint64_t
n
)
{
return
std
::
to_string
(
(
n
>>
24
)
&
255
)
+
"."
+
std
::
to_string
(
(
n
>>
16
)
&
255
)
+
"."
+
std
::
to_string
(
(
n
>>
8
)
&
255
)
+
"."
+
std
::
to_string
(
n
&
255
)
;
}
void
describe
(
const
std
::
string
&
cidr
)
{
size_t slash
=
cidr
.
find
(
'/'
)
;
int
prefix
=
std
::
stoi
(
cidr
.
substr
(
slash
+
1
)
)
;
uint64_t
mask
=
(
0xFFFFFFFFull
<<
(
32
-
prefix
)
)
&
0xFFFFFFFFull
;
uint64_t
network
=
toInt
(
cidr
.
substr
(
0
,
slash
)
)
&
mask
;
uint64_t
broadcast
=
network
|
(
~
mask
&
0xFFFFFFFFull
)
;
std
::
string rows
[
6
]
[
2
]
=
{
{
"mask"
,
toIp
(
mask
)
}
,
{
"network"
,
toIp
(
network
)
}
,
{
"broadcast"
,
toIp
(
broadcast
)
}
,
{
"first host"
,
toIp
(
network
+
1
)
}
,
{
"last host"
,
toIp
(
broadcast
-
1
)
}
,
{
"hosts"
,
std
::
to_string
(
(
1ull
<<
(
32
-
prefix
)
)
-
2
)
}
,
}
;
std
::
printf
(
"%s\n"
,
cidr
.
c_str
(
)
)
;
for
(
auto
&
row
:
rows
)
std
::
printf
(
"  %-11s%s\n"
,
row
[
0
]
.
c_str
(
)
,
row
[
1
]
.
c_str
(
)
)
;
}
int
main
(
)
{
describe
(
"192.168.10.150/26"
)
;
describe
(
"172.16.45.200/20"
)
;
return
0
;
}
```

Output

```
192.168.10.150/26
  mask       255.255.255.192
  network    192.168.10.128
  broadcast  192.168.10.191
  first host 192.168.10.129
  last host  192.168.10.190
  hosts      62
172.16.45.200/20
  mask       255.255.240.0
  network    172.16.32.0
  broadcast  172.16.47.255
  first host 172.16.32.1
  last host  172.16.47.254
  hosts      4094
```

### VLSM: subnets of different sizes

Equal subnets waste addresses when needs differ. Variable Length Subnet Masking gives each subnet the smallest prefix that fits, allocating the largest first so every block stays aligned.

Task. From 192.168.10.0/24, serve a LAN of 100 hosts, a LAN of 50, a LAN of 20 and a point-to-point router link needing 2.

Addresses 192.168.10.228 to .255 stay free for later. With equal /26 subnets, the 100-host LAN would not have fitted at all.

Sort the needs largest first. 100 hosts need 7 host bits, because 2^7 − 2 = 126 is the first that fits, so a /25 of 128 addresses at .0, hosts .1 to .126.

- Sort the needs largest first. 100 hosts need 7 host bits, because 2^7 − 2 = 126 is the first that fits, so a /25 of 128 addresses at .0, hosts .1 to .126.
- 50 hosts fit in 2^6 − 2 = 62: a /26. The next free address, .128, is a multiple of 64, so the block starts there, hosts .129 to .190.
- 20 hosts fit in 2^5 − 2 = 30: a /27. The next free address, .192, is a multiple of 32, so the block starts there, hosts .193 to .222.
- The router link needs 2 addresses, so a /30 of 4 at .224. Because each block went largest first, every one started on a multiple of its size, and .228 to .255 stay free for later.

### Supernetting (route aggregation)

Supernetting is the reverse: combining contiguous networks into one shorter prefix so a router advertises one route instead of many. The four networks 192.168.0.0/24 to 192.168.3.0/24 share their first 22 bits, so they summarise as 192.168.0.0/22 . The networks must be contiguous, their count must be a power of 2, and the first network must start on a multiple of the block (here the third octet 0 is a multiple of 4). 192.168.1.0 to 192.168.4.0 cannot form one /22, because 1 is not a multiple of 4.

The four third octets differ only in their last 2 bits, so the first 22 bits are shared and one route, 192.168.0.0/22, covers all four and nothing else.

- The four third octets differ only in their last 2 bits, so the first 22 bits are shared and one route, 192.168.0.0/22, covers all four and nothing else.
- Shift the set by one and the third octets 1 to 4 agree only in their first 5 bits. The shared prefix shrinks to /21, a block of 8 networks from 192.168.0.0, so these four cannot be one route.

### IPv4 vs IPv6

IPv4's 4.3 billion addresses ran out (IANA handed out its last free /8 blocks in 2011), and NAT has stretched them since. IPv6 is the long-term fix.

IPv6 shortening rules: drop leading zeros in each group, then replace one run of all-zero groups with :: . So 2001:0db8:0000:0000:0000:0000:0000:0001 becomes 2001:db8:0:0:0:0:0:1 and then 2001:db8::1. Using :: twice would make the address ambiguous.

### Common mistakes

- Using 2^h for usable hosts: subtract 2 (network and broadcast), except on /31 and /32.
- Treating a host address as a network address: 192.168.10.100/26 is a host in 192.168.10.64/26, not a network.
- Mixing the old rule of 2^s − 2 subnets (no "subnet zero") with the modern 2^s; say which you use.
- Calling 172.32.0.1 private: the 172.16.0.0/12 range ends at 172.31.255.255.
- Forgetting VLSM order: allocate the largest subnet first, or blocks end up misaligned.
- Writing :: twice in an IPv6 address.

### Interview questions

Find the network, broadcast and host range of 192.168.1.77/27. /27 leaves 5 host bits, so the block size is 32 and subnets start at .0, .32, .64, .96. 77 lies between 64 and 95, so the network is 192.168.1.64, the broadcast 192.168.1.95, and hosts .65 to .94, which is 30 usable addresses.

How many subnets and hosts per subnet do you get by dividing a /24 into /28s? Four bits are borrowed, giving 2^4 = 16 subnets. Each has 4 host bits: 16 addresses and 14 usable hosts.

Why was CIDR introduced? Classful addressing wasted addresses (class B was too big for most and class C too small) and filled routing tables with one entry per class C network. CIDR allows any prefix length and lets contiguous blocks be advertised as one aggregate route.

What is the difference between a public and a private IP address? A public address is globally unique and routable on the internet. A private address (10/8, 172.16/12, 192.168/16) is reused inside many organisations and is not routed publicly, so traffic to the internet passes through NAT, which swaps it for a public address.

What is 127.0.0.1 used for? It is the loopback address: packets sent to it never leave the machine. It is used to test the local TCP/IP stack and to reach services running on the same computer, such as a development server on localhost.

Which prefix would you use on a point-to-point link between two routers? Traditionally a /30, which has exactly two usable addresses. RFC 3021 also allows a /31 on point-to-point links, using both addresses since no broadcast is needed, which saves address space.

How do you shorten an IPv6 address? Remove leading zeros in each 16-bit group, then replace the longest single run of consecutive zero groups with :: , once per address. Each group is four hexadecimal digits, eight groups in all.

Next, read TCP and UDP , and test your subnetting with the Computer Networks (Intermediate) skill test .

### How many usable hosts are there in a /24 network?

254. A /24 leaves 8 host bits, which give 2^8 = 256 addresses. The first (all host bits 0) is the network address and the last (all host bits 1) is the broadcast address, so 256 − 2 = 254 can be assigned to hosts.

### What are the private IP address ranges?

RFC 1918 reserves three IPv4 blocks for private networks: 10.0.0.0/8 (10.0.0.0 to 10.255.255.255), 172.16.0.0/12 (172.16.0.0 to 172.31.255.255) and 192.168.0.0/16 (192.168.0.0 to 192.168.255.255). They are not routed on the public internet, so hosts using them reach it through NAT.

### How do you find the network address from an IP address and subnet mask?

Do a bitwise AND of the address and the mask. For 192.168.10.150 with mask 255.255.255.192, only the last octet matters: 150 AND 192 is 10010110 AND 11000000 = 10000000 = 128, so the network address is 192.168.10.128.

### What is CIDR notation?

Classless Inter-Domain Routing writes an address with a slash and the number of network bits, such as 192.168.1.0/24, instead of relying on the address class. Prefixes can be any length, so networks can be sized to need, and contiguous networks can be summarised as one route.

### What is the difference between IPv4 and IPv6?

IPv4 addresses are 32 bits written in dotted decimal, giving about 4.3 billion addresses. IPv6 addresses are 128 bits written in hexadecimal groups separated by colons. IPv6 also has a fixed 40-byte header, no broadcast, no header checksum and built-in address auto-configuration.

### Why do we subtract 2 when counting usable hosts in a subnet?

Two addresses in every subnet are reserved: the one with all host bits 0 names the network itself, and the one with all host bits 1 is the directed broadcast address. The exceptions are /31 point-to-point links, which use both addresses (RFC 3021), and /32, a single host route.


---

## Module 6: Routing and Routing Protocols

*Original URL: https://codekairo.com/notes/computer-networks/routing-algorithms*

### Overview

Quick answer

### What is routing in computer networks?

Routing is how a network decides the path packets take from one network to another. Routers build routing tables, either configured by hand (static routing) or learned from routing protocols (dynamic routing), and forward each packet to the next hop of the entry with the longest matching prefix. Distance vector protocols such as RIP use the Bellman-Ford algorithm; link state protocols such as OSPF use Dijkstra's algorithm.

- Routing vs forwarding
- The routing table and longest prefix match
- Static vs dynamic routing
- Distance vector routing (Bellman-Ford)
- Link state routing (Dijkstra)
- Distance vector vs link state
- Interior and exterior gateway protocols
- RIP vs OSPF vs BGP
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A packet crossing the internet passes through a dozen or more routers, and each one makes a decision on its own: which neighbour should get this packet next? Routing is how those decisions are prepared. Routers run algorithms that learn the network's shape, compute good paths and write the results into routing tables; forwarding then uses those tables, packet by packet. This note covers the table itself, the two families of routing algorithm with worked examples, and the three protocols interviewers name: RIP, OSPF and BGP.

### The routing table and longest prefix match

Each entry says: for destinations in this prefix, send to this next hop through this interface. A router may hold overlapping entries and picks the longest matching prefix , the most specific route.

10.1.2.5 matches 4 entries (/8, /16, /24, /0). The longest prefix, 10.1.2.0/24, is the most specific route and wins: next hop 192.168.3.2 on eth3.

- 10.1.2.5 matches 4 entries (/8, /16, /24, /0). The longest prefix, 10.1.2.0/24, is the most specific route and wins: next hop 192.168.3.2 on eth3.
- 10.1.9.9 matches 3 entries (/8, /16, /0). The longest prefix, 10.1.0.0/16, is the most specific route and wins: next hop 192.168.2.2 on eth2.
- 10.9.9.9 matches 2 entries (/8, /0). The longest prefix, 10.0.0.0/8, is the most specific route and wins: next hop 192.168.1.2 on eth1.
- 8.8.8.8 matches only the default route, 0.0.0.0/0, which matches every address with zero bits. Nothing more specific exists, so it goes to the ISP at 203.0.113.1.

The default route (0.0.0.0/0) matches everything with a prefix length of zero, so it is used only when nothing more specific matches. A home router's table is little more than its LAN plus a default route to the ISP. The prefixes themselves come from IP addressing and subnetting .

### Static vs dynamic routing

On Cisco routers, when two sources offer a route to the same prefix , the one with the lower administrative distance wins: directly connected 0, static 1, eBGP 20, OSPF 110, RIP 120. The prefix length is compared first, so a more specific route always beats a more trusted but shorter one.

### Distance vector routing (Bellman-Ford)

Each router keeps a distance vector : its best-known cost to every destination and the next hop for it. Periodically, and whenever something changes, it sends this vector to its neighbours only . On receiving vectors, router x recomputes, for every destination y:

D(x, y) = min over each neighbour v of [ cost(x, v) + D(v, y) ]

This is the Bellman-Ford equation, run in a distributed way: no router ever sees the whole map.

### Worked example

Four routers with these link costs: A–B 2, A–C 5, B–C 1, C–D 2. In each round, every router recomputes its vector from its neighbours' vectors of the round before.

Round 0: each router knows only its own links. B's vector is (A 2, B 0, C 1, D ∞) and C's is (A 5, B 1, C 0, D 2); D is unreachable from A and B because neither touches it.

- Round 0: each router knows only its own links. B's vector is (A 2, B 0, C 1, D ∞) and C's is (A 5, B 1, C 0, D 2); D is unreachable from A and B because neither touches it.
- Round 1: every router adds its link cost to each neighbour's round-0 vector and keeps the minimum. A finds C cheaper through B, 2 + 1 = 3, than over its own link (5), and reaches D for the first time at 5 + 2 = 7 via C. 6 entries change.
- Round 2: B learned D at cost 3 in round 1, and that news reaches A now: 2 + 3 = 5 via B beats 7 via C, so A switches its route to D. 2 entries change.
- Round 3: recomputing from round 2's vectors changes nothing anywhere, so the network has converged. No router ever saw the whole map, only its neighbours' distances.

A's vector as the rounds go by, the numbers to write on paper:

A third round changes nothing: the network has converged . Notice that A's best route to D needed two rounds, because B had to learn D before it could tell A.

### The count-to-infinity problem

Good news travels fast in distance vector routing; bad news travels slowly. Take a line A–B–C with every link cost 1, and let the B–C link fail.

Before the failure, every link costs 1: B reaches C directly at cost 1, and A reaches C through B at cost 2.

- Before the failure, every link costs 1: B reaches C directly at cost 1, and A reaches C through B at cost 2.
- The B–C link fails. B drops its direct route, but A is still advertising cost 2 to C, and nothing in that number says the path runs through B itself.
- B believes A's advertisement and sets its cost to C to 1 + 2 = 3 via A — a route that loops straight back through B.
- A hears B's 3 and raises its own cost to 4. Each exchange adds one link's cost, and each router's route points at the other.
- B hears A's 4 and raises its own cost to 5. Each exchange adds one link's cost, and each router's route points at the other.
- They keep counting, one exchange at a time, until the cost reaches RIP's infinity, 16: 15 exchanges in all before both routers finally agree that C is unreachable.
- With split horizon, A never advertises C to B, because B is A's next hop for it. B has no route the moment the link fails, and A hears that C is unreachable in the next exchange: 2 exchanges instead of 15.

B believes A's advertisement, not knowing that A's route goes through B itself, and the two count upwards until the cost reaches "infinity", which RIP defines as 16 . The fixes:

- Split horizon : never advertise a route back to the neighbour you learned it from. A would not tell B about C at all.
- Poison reverse : advertise it back, but with cost ∞, so B knows at once that A has no independent path.
- Hold-down timers ignore new information about a failed route for a while, and triggered updates send bad news immediately instead of waiting for the next periodic update.

Split horizon fixes two-router loops but not every loop among three or more routers; the hop limit is the final backstop.

### Link state routing (Dijkstra)

In link state routing each router:

- discovers its neighbours (with hello messages) and measures the cost of each link;
- builds a link state advertisement (LSA) describing its own links;
- floods the LSA to every router in the area, so all routers hold an identical link state database , a full map;
- runs Dijkstra's shortest path first algorithm with itself as the source and installs the resulting next hops.

### Worked example

Five routers with these link costs: A–B 4, A–C 2, B–C 1, B–D 5, C–D 8, C–E 10, D–E 2. Router A runs Dijkstra: at each step it settles the unsettled node with the smallest tentative distance and relaxes that node's links. On paper, write one row per step: the node settled, then every other node's current distance and predecessor.

Router A holds the full map from the flooded link state advertisements and runs Dijkstra with itself as the source: its own distance is 0, every other router starts at ∞.

- Router A holds the full map from the flooded link state advertisements and runs Dijkstra with itself as the source: its own distance is 0, every other router starts at ∞.
- Settle A at 0 and relax its links: B gets 4, C gets 2.
- The smallest unsettled distance is C at 2, so it is settled. Relaxing its links: B improves from 4 to 2 + 1 = 3, D gets 10, E gets 12.
- The smallest unsettled distance is B at 3, so it is settled. Relaxing its links: D improves from 10 to 3 + 5 = 8.
- The smallest unsettled distance is D at 8, so it is settled. Relaxing its links: E improves from 12 to 8 + 2 = 10.
- Settle E at 10, the last router. Every distance is now final: a settled node is never improved, because all links have non-negative cost.
- The shortest paths form a tree rooted at A, and A installs only the first hop of each: every destination goes via C. The links on no shortest path at all are A–B (4), C–D (8) and C–E (10), the direct A–B link among them.

A's routing table:

Every next hop is C, and the direct A–B link (cost 4) is not used at all. The algorithm itself is covered in depth in the Dijkstra's algorithm lesson .

### Interior and exterior gateway protocols

The internet is made of autonomous systems (ASes) : networks run by one organisation under one routing policy, each with an AS number. Routing works at two levels:

- Interior gateway protocols (IGPs) route inside one AS and look for the best path by a metric: RIP, OSPF, IS-IS and Cisco's EIGRP.
- Exterior gateway protocols route between ASes. The only one in use is BGP (version 4). It is a path vector protocol: each route carries the list of ASes it has passed through, so a router that sees its own AS number in the list rejects the route, which prevents loops. Routes are chosen by policy (business relationships, preferences) rather than by shortest distance. BGP between ASes is eBGP; BGP carrying those routes inside one AS is iBGP.

### RIP vs OSPF vs BGP

OSPF's areas keep flooding and Dijkstra runs local: routers in one area hold the full map only of that area, plus summaries of the others through the backbone.

### Common mistakes

- Choosing a route by administrative distance before prefix length: the longest prefix is compared first.
- Saying distance vector routers know the topology: they know only distances and next hops.
- Saying RIP's limit is 16 hops: 15 is the maximum usable; 16 means unreachable.
- Calling BGP a distance vector protocol: it is path vector, and it chooses by policy.
- In Dijkstra, settling a node before it has the smallest tentative distance, or forgetting to update a neighbour that improves.
- Assuming split horizon prevents every routing loop: it fixes only loops between two routers.

### Interview questions

How does a router choose between overlapping routes to a destination? First by longest prefix match: the most specific matching entry wins. If two sources offer the same prefix, the lower administrative distance wins (on Cisco, static 1 beats OSPF 110, which beats RIP 120). Within one protocol, the lower metric wins.

Explain count-to-infinity and how split horizon helps. After a link fails, two distance vector routers can each believe the other still has a path, and they raise their costs by one link at a time until they hit the protocol's infinity. Split horizon stops a router from advertising a route back to the neighbour it learned it from, which removes the false path between two routers.

Why does OSPF converge faster than RIP? OSPF floods link changes to every router at once and each router recomputes its paths from a complete map, so news spreads in one flooding wave. RIP passes changes only between neighbours, often on a 30-second timer, and can count to infinity before settling.

Why does OSPF divide a network into areas? In a large network, flooding every change everywhere and rerunning Dijkstra on a huge map costs bandwidth, memory and CPU. Areas confine detailed link state to each area and exchange only summaries through backbone area 0, which keeps databases small and contains instability.

What is BGP, and why is it called a path vector protocol? BGP is the protocol autonomous systems use to exchange reachability across the internet. Each advertisement carries the full list of ASes on the path, which lets routers detect loops and apply policies, such as preferring a customer's routes or avoiding a particular network.

Why does RIP limit paths to 15 hops? To bound count-to-infinity: with 16 defined as unreachable, a counting loop ends after a limited number of exchanges. The cost is that RIP cannot serve networks wider than 15 hops, one reason larger networks use OSPF.

What is a default route, and when is it used? A default route, 0.0.0.0/0, matches every destination with the shortest possible prefix, so it is used only when no more specific route matches. Edge networks use it to send all internet-bound traffic to their ISP without holding the full internet routing table.

Next, read the data link layer , and test the algorithms with the Computer Networks (Intermediate) skill test .

### What is the difference between routing and forwarding?

Routing is the network-wide process of computing paths and filling the routing table, done by routing protocols in the router's control plane whenever the topology changes. Forwarding is the per-packet action of looking up the destination and moving the packet to the right output interface, done in nanoseconds in the data plane.

### What is the difference between distance vector and link state routing?

In distance vector routing each router shares its table of distances only with its neighbours and computes routes with Bellman-Ford, so it knows distances but not the topology. In link state routing each router floods the state of its own links to all routers, builds the full map and runs Dijkstra. Link state converges faster and avoids count-to-infinity.

### What is the count-to-infinity problem?

When a link fails in a distance vector network, routers can keep learning stale routes to the lost destination from each other, each time adding the link cost, so the distance creeps upwards one exchange at a time until it reaches the protocol's infinity. RIP caps this at 16. Split horizon and poison reverse prevent it between two routers.

### What is longest prefix matching?

When several routing table entries match a destination address, the router uses the most specific one, with the longest prefix. For 10.1.2.5, an entry for 10.1.2.0/24 beats 10.1.0.0/16, which beats 10.0.0.0/8, and the default route 0.0.0.0/0 is used only when nothing else matches.

### What is an autonomous system in networking?

An autonomous system is a network, or group of networks, run by one organisation with a single routing policy, such as an ISP, a cloud provider or a large university. It is identified by an AS number. Interior protocols like OSPF route inside one; BGP routes between them.

### What is the difference between RIP, OSPF and BGP?

RIP is a distance vector interior protocol using hop count, limited to 15 hops. OSPF is a link state interior protocol using bandwidth-based costs, Dijkstra and areas, and it converges quickly. BGP is a path vector exterior protocol that connects autonomous systems across the internet and chooses routes by policy rather than shortest distance.


---

## Module 7: TCP and UDP

*Original URL: https://codekairo.com/notes/computer-networks/tcp-and-udp*

### Overview

Quick answer

### What is the difference between TCP and UDP?

TCP (Transmission Control Protocol) is connection-oriented and reliable: it opens a connection with a three-way handshake, numbers every byte, retransmits lost data, delivers bytes in order and controls flow and congestion. UDP (User Datagram Protocol) is connectionless and best effort: it sends independent datagrams with an 8-byte header and no guarantees, so it is lighter and faster. Web pages use TCP; DNS queries, calls and games often use UDP.

- What the transport layer does
- The UDP datagram
- The TCP segment
- Opening a connection: the three-way handshake
- Closing a connection: the four-way termination
- Reliability: sequence numbers, ACKs and retransmission
- Flow control: the sliding window
- Congestion control
- TCP vs UDP
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The network layer gets a packet to the right machine; the transport layer gets the data to the right program on that machine. The internet offers two main transport protocols with opposite philosophies. TCP turns IP's unreliable packets into a reliable, ordered stream of bytes and pays for it with setup time and overhead. UDP adds almost nothing to IP and leaves reliability, if it is needed at all, to the application. Interviewers ask about both, and about the handshake and windows in detail.

### What the transport layer does

- Process-to-process delivery using 16-bit port numbers (0 to 65,535).
- Multiplexing and demultiplexing : many applications on one host share the network, and each arriving segment is handed to the right socket.
- In TCP only: connection setup and teardown, reliability, ordering, flow control and congestion control.

A socket is one endpoint: an IP address plus a port. A TCP connection is identified by four values (source IP, source port, destination IP, destination port), so one web server on port 443 can hold thousands of connections at once: each comes from a different client address or port.

### The UDP datagram

UDP's header is a fixed 8 bytes ; TCP's is 20 bytes before options. Side by side:

Both start with the two 16-bit ports. UDP adds only a length and a checksum: 8 bytes. TCP adds the sequence and acknowledgement numbers, flags and window: 20 bytes, and its 4-bit length counts 32-bit words, so options can take it to 60.

That is all. No connection, no sequence numbers, no acknowledgements. Each sendto call produces one datagram, and the receiver gets it whole or not at all, so UDP preserves message boundaries . A lost or reordered datagram is the application's problem.

### The TCP segment

The flags that matter most: SYN opens a connection, ACK says the acknowledgement number is valid, FIN says "I have no more data", RST aborts a connection at once, and PSH asks the receiver to pass data to the application without waiting. TCP numbers bytes, not segments , and SYN and FIN each consume one sequence number.

### Opening a connection: the three-way handshake

Suppose the client picks an initial sequence number (ISN) of 100 and the server picks 300. Real ISNs are unpredictable 32-bit values, chosen so old or forged segments are unlikely to fit.

The client sends a SYN carrying its initial sequence number, 100, and enters SYN_SENT. The server, listening, receives it and enters SYN_RECEIVED.

- The client sends a SYN carrying its initial sequence number, 100, and enters SYN_SENT. The server, listening, receives it and enters SYN_RECEIVED.
- The server answers SYN-ACK: its own ISN, 300, and ack 101, because the SYN used up number 100 and 101 is the next byte it expects. On receipt the client is ESTABLISHED.
- The client acknowledges the server's ISN with ack 301; its seq is 101, and data may ride in this very segment. The server is now ESTABLISHED too: each side has announced its ISN and heard it acknowledged.

In short: SYN (seq = 100), SYN-ACK (seq = 300, ack = 101), ACK (seq = 101, ack = 301).

Three messages are the minimum because each side must announce its own ISN and hear it acknowledged . With only two, the server could never be sure the client received its ISN, and an old duplicate SYN arriving late could open a connection nobody asked for.

### Closing a connection: the four-way termination

TCP is full-duplex, so each direction is closed separately with its own FIN. Between the two FINs one direction is closed while the other may still carry data: a half-close . Suppose the client's next sequence number is 500, the server's is 800, and the server has no more data to send.

The client has no more data and sends FIN, seq 500: FIN_WAIT_1. The server's TCP receives it and moves to CLOSE_WAIT, waiting for its application to finish.

- The client has no more data and sends FIN, seq 500: FIN_WAIT_1. The server's TCP receives it and moves to CLOSE_WAIT, waiting for its application to finish.
- The server acknowledges at once, ack 501, since the FIN used number 500. The client is in FIN_WAIT_2: its direction is closed, but the server may still send data, a half-close.
- When its application closes, the server sends its own FIN, seq 800, and enters LAST_ACK. The client, receiving it, enters TIME_WAIT.
- The client's final ACK, ack 801, reaches the server, which closes. Steps 2 and 3 often travel as one segment, giving three in all.
- The client waits two maximum segment lifetimes before closing, in case its last ACK was lost and the FIN comes again, and so stray segments of this connection die out first.

The side that closes first waits in TIME_WAIT for twice the maximum segment lifetime (2 × MSL; Linux uses a fixed 60 seconds): if its last ACK is lost, the server will resend its FIN and the client must still be there to answer, and delayed segments of this connection must die out before the same four values are reused.

### Reliability: sequence numbers, ACKs and retransmission

TCP's acknowledgements are cumulative : "ack = 1,101" means "I have every byte before 1,101". Take the connection above, where the client's data starts at byte 101, and send five segments of 1,000 bytes. Segment 2 is lost.

The sender's data starts at byte 101, in segments of 1,000 bytes. The first arrives and the receiver acknowledges 1,101: it holds every byte before that.

- The sender's data starts at byte 101, in segments of 1,000 bytes. The first arrives and the receiver acknowledges 1,101: it holds every byte before that.
- The second segment, bytes 1,101 to 2,100, is lost on the way. Nothing tells the sender yet, and it keeps sending while its window allows.
- Segment 3 arrives with a gap before it. The receiver buffers it but can only repeat ACK 1,101, since acknowledgements are cumulative: a duplicate ACK.
- Segments 4 and 5 arrive and are buffered too, and each brings another ACK 1,101. Three duplicates say one segment is missing while later ones get through.
- The sender resends seq 1,101 at once instead of waiting for its timer. It fills the gap, and the receiver acknowledges 5,101 in one go because the rest was already buffered.

The sender learns of the loss in one of two ways:

- Timeout. Each unacknowledged segment has a retransmission timer (RTO), computed from a smoothed RTT estimate plus a margin for its variation. When it expires, the segment is resent and the RTO doubles.
- Fast retransmit. Three duplicate ACKs strongly suggest one segment was lost while later ones arrived, so the sender resends it at once without waiting for the timer, as above.

Once the gap is filled the receiver acknowledges 5,101 in one go, because bytes 2,101 to 5,100 were already buffered. With the SACK option, the receiver can also say exactly which blocks it holds, so only missing data is resent.

### Flow control: the sliding window

The receiver has a finite buffer. In every segment it advertises rwnd , the free space left, and the sender keeps the bytes sent-but-unacknowledged at or below it. When rwnd is 0 the sender stops and probes with small segments on the persist timer . Number the bytes from 1 for simplicity and take a 4,000-byte buffer with a 1,000-byte maximum segment size (MSS):

The buffer is empty, so the receiver advertises 4,000 bytes. The sender sends four segments and must then stop, whatever its own speed.

- The buffer is empty, so the receiver advertises 4,000 bytes. The sender sends four segments and must then stop, whatever its own speed.
- All four arrived, but the application has read only 1,000 bytes, so 3,000 sit in the buffer and the window is 1,000. The window slides on to segment 5.
- Segment 5 fills the buffer and the application has stopped reading: the window is 0. The sender stops, probing now and then with a tiny segment so it hears when space opens.
- The application reads 2,000 bytes, the receiver advertises a window of 2,000, and the sender may send two more segments.

The window "slides" forward as acknowledgements arrive. The 16-bit field caps rwnd at 65,535 bytes, so fast long links use the window scale option to multiply it.

### Congestion control

Flow control protects the receiver; congestion control protects the network. The sender keeps a congestion window (cwnd) and may have at most min(rwnd, cwnd) bytes in flight. The classic algorithm (TCP Reno, the textbook model) has these parts:

- Slow start. cwnd starts small (1 MSS in the textbook; modern stacks such as Linux start at 10 MSS) and grows by 1 MSS for every ACK, so it doubles every RTT , until it reaches the slow-start threshold ssthresh .
- Congestion avoidance. Above ssthresh, cwnd grows by about 1 MSS per RTT (additive increase).
- On a timeout : ssthresh = cwnd / 2, cwnd = 1 MSS, and slow start begins again (both Tahoe and Reno).
- On three duplicate ACKs : fast retransmit the lost segment; Reno then sets ssthresh = cwnd / 2 and continues from cwnd = ssthresh ( fast recovery ), skipping slow start. Tahoe drops cwnd to 1 MSS instead.

### Worked example

Initial ssthresh = 16 MSS, cwnd starts at 1 MSS, and a timeout happens in round 9.

The timeout at cwnd = 20 sets ssthresh = 10 and cwnd = 1, and the second slow start stops at the new threshold : 10 in round 14, not 16. Three duplicate ACKs instead would have let Reno continue from cwnd = 10 in round 10.

Slow start doubles cwnd every round, 1, 2, 4, 8, until it reaches ssthresh = 16 in round 5. From there congestion avoidance adds one MSS a round: 17, 18, 19, 20.

- Slow start doubles cwnd every round, 1, 2, 4, 8, until it reaches ssthresh = 16 in round 5. From there congestion avoidance adds one MSS a round: 17, 18, 19, 20.
- A timeout in round 9, at cwnd = 20, halves the threshold to 10 and drops cwnd to 1. Slow start runs again but stops at the new threshold: 10, not 16, in round 14, then grows by one a round.
- Had three duplicate ACKs signalled the loss instead, Reno would halve the threshold the same way but continue from cwnd = 10 (fast recovery), skipping slow start: the sawtooth of AIMD.

This sawtooth is called AIMD (additive increase, multiplicative decrease). Linux's default algorithm today is CUBIC, which grows cwnd as a cubic function of time since the last loss, but interview questions use the Reno model above.

### TCP vs UDP

Real-time media prefers UDP because a late packet is useless: replaying a lost 20 ms of audio after a retransmission would only add delay.

### Common mistakes

- Saying the acknowledgement number is the sequence number received: it is the next byte expected .
- Forgetting that SYN and FIN each consume one sequence number (ISN 100 is acknowledged with 101).
- Claiming UDP has no checksum: it has one, optional only in IPv4.
- Confusing flow control (receiver's buffer, rwnd) with congestion control (the network, cwnd).
- Saying TCP preserves message boundaries: two writes of 100 bytes may arrive as one read of 200.
- Letting slow start overshoot ssthresh after a timeout: cwnd stops at the threshold, then grows linearly.

### Interview questions

Why is the TCP handshake three-way and not two-way? Both sides must announce an initial sequence number and receive an acknowledgement for it. Two messages acknowledge only the client's number, leaving the server unsure the client received its own; the third message closes that gap and protects against old duplicate SYNs opening stale connections.

What happens if the final ACK of the handshake is lost? The server stays in SYN_RECEIVED and retransmits its SYN-ACK after a timeout; the client answers with another ACK. If the client has already started sending data, the server accepts it, since every data segment also carries the acknowledgement it was waiting for.

What is TIME_WAIT, and why does it last 2 × MSL? It is the state the side that closes first enters after sending the final ACK. Waiting two maximum segment lifetimes lets it re-acknowledge a retransmitted FIN if its last ACK was lost, and lets stray segments of the old connection expire before the same address and port pair is reused.

What is a SYN flood, and how do SYN cookies help? An attacker sends many SYNs, often from spoofed addresses, and never completes the handshake, filling the server's queue of half-open connections. With SYN cookies, the server keeps no state for a SYN; it encodes the connection details in its own ISN and rebuilds them only when a valid final ACK returns.

What triggers fast retransmit? Three duplicate ACKs for the same number. They mean later segments are arriving while one is missing, so the sender resends that segment immediately rather than waiting for the retransmission timer.

Why does DNS use UDP? A query and its answer usually fit in one small datagram each, so a TCP handshake would double the time for little benefit. The resolver simply retries on loss. DNS switches to TCP when an answer is too large or for zone transfers.

Can two clients connect to the same server port at the same time? Yes. A TCP connection is identified by source IP, source port, destination IP and destination port. Clients differ in address or source port, so thousands of connections can share the server's port 443.

How is the amount of data a TCP sender may have in flight decided? It is the minimum of the receiver's advertised window (rwnd, flow control) and the sender's congestion window (cwnd, congestion control). Whichever is smaller limits the sender.

Next, read DNS , and test the handshakes and windows with the Computer Networks (Intermediate) skill test .

### What is the TCP three-way handshake?

It is how TCP opens a connection. The client sends a SYN with its initial sequence number, the server replies with a SYN-ACK carrying its own initial sequence number and acknowledging the client's, and the client sends an ACK. Both sides then know each other's starting numbers and the connection is established.

### Why is UDP faster than TCP?

UDP has no connection setup, so data goes in the very first packet, while TCP spends a round trip on the handshake. UDP also has no acknowledgements, retransmissions, ordering or congestion control slowing the sender, and its header is 8 bytes instead of TCP's 20 to 60.

### What is the size of the TCP and UDP headers?

The UDP header is always 8 bytes: source port, destination port, length and checksum. The TCP header is 20 bytes without options and up to 60 bytes with them, because its 4-bit header length field counts 32-bit words, at most 15 × 4 = 60 bytes.

### What is the difference between flow control and congestion control in TCP?

Flow control protects the receiver: the receiver advertises a window (rwnd) of free buffer space and the sender never has more unacknowledged data than that. Congestion control protects the network: the sender keeps its own congestion window (cwnd), grown and cut by slow start and congestion avoidance. The sender obeys the smaller of the two.

### Which applications use TCP and which use UDP?

TCP carries web traffic over HTTP/1.1 and HTTP/2, email (SMTP, IMAP, POP3), file transfer (FTP), SSH and database connections, where every byte must arrive. UDP carries DNS queries, DHCP, VoIP and video calls, online games, live streaming and QUIC, the transport under HTTP/3.


---

## Module 8: Domain Name System (DNS)

*Original URL: https://codekairo.com/notes/computer-networks/dns*

### Overview

Quick answer

### What is DNS and how does it work?

DNS (Domain Name System) is the internet's distributed directory that translates domain names such as www.example.com into IP addresses. Your computer asks a recursive resolver, which asks a root server, then the top-level domain's servers, then the domain's authoritative server, and caches the answer for its TTL. DNS normally runs over UDP port 53, switching to TCP for large answers and zone transfers.

- Why DNS is distributed
- The DNS hierarchy
- Who takes part in a lookup
- Worked example: resolving www.example.com
- Recursive vs iterative queries
- DNS record types
- Caching and TTL
- DNS over UDP and TCP, port 53
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Computers route packets by IP address, but people remember names. DNS is the system that maps one to the other, and it runs every time you open a website, send an email or call an API. In the early ARPANET, every host downloaded one shared file of names and addresses; that stopped scaling, and DNS replaced it in the 1980s with a distributed, hierarchical, cached database (its core specification is RFC 1034 and 1035, from 1987). No single server knows every name, yet any name can be found in a handful of queries.

### Why DNS is distributed

DNS does more than turn names into addresses. It also gives one server many names (aliases), tells senders where to deliver a domain's email (MX records), spreads load by returning different addresses to different clients, and holds verification text for services. A single central database would be a single point of failure, a traffic bottleneck and an administrative nightmare. So DNS splits the namespace into zones , each managed by its owner's authoritative name servers , and lets everyone cache answers.

### The DNS hierarchy

Names form a tree read from right to left. A fully qualified domain name (FQDN) ends with a dot for the root: www.example.com.

Each label of a name is one level of the tree, read from the right: the unnamed root, then 3 top-level domains here, then the names under them. Each level delegates the one below, so the root only knows who runs com, and com only who runs example.com.

TLDs are generic (gTLDs: .com , .org , .net , and newer ones such as .app ) or country-code (ccTLDs: .in , .jp , .uk ). Each level delegates the level below it: the root zone lists the name servers for com , the com zone lists the name servers for example.com , and example.com 's own servers hold its records. Each root identity is served from many places at once through anycast , where the same IP address is announced from many sites and routing picks the nearest.

### Who takes part in a lookup

- Stub resolver : the small DNS client in your operating system. It asks one question and expects a final answer.
- Recursive resolver : the server that does the work, run by your ISP, your company or a public service such as 8.8.8.8 or 1.1.1.1. Its address usually arrives through DHCP.
- Root, TLD and authoritative servers : each answers only for its own part of the tree.

### Worked example: resolving www.example.com

Assume every cache is empty and the website's address is 203.0.113.10. The browser checks its own cache, then the operating system its cache and the hosts file; all miss, so the stub resolver asks the recursive resolver. A server that does not hold the answer returns a referral : the NS records of the servers one level down, plus their IP addresses (called glue ) so the resolver can reach them.

Every cache is empty. Your computer's stub resolver sends one recursive query, recursion desired, to its resolver: give me the A record for www.example.com, the final answer and nothing less.

- Every cache is empty. Your computer's stub resolver sends one recursive query, recursion desired, to its resolver: give me the A record for www.example.com, the final answer and nothing less.
- The resolver starts at a root server. The root does not know the answer but returns a referral: the name servers for com, with their addresses (glue).
- It asks a com TLD server the same question and gets another referral, to the servers for example.com. Each of these queries is iterative: the server answers from what it holds and the resolver does the chasing.
- The zone's authoritative server, ns1.example.com, answers: www.example.com A 203.0.113.10, TTL 3600.
- The resolver caches the answer and both referrals, and returns the address to your computer, which caches it too: one question from your computer cost 3 queries upstream.

Many resolvers send each server only the part of the name it needs (QNAME minimisation), so the root sees "com" rather than the full name.

### Recursive vs iterative queries

In a recursive query the asker sends 1 message and waits while each server asks the next, 6 messages in all. In an iterative one each server only refers, so the asker sends 3 queries itself. Your stub asks recursively; resolvers ask iteratively.

Root and TLD servers never resolve recursively; they would be overwhelmed.

### DNS record types

Two rules catch people out. A name with a CNAME may have no other records, so the zone apex ( example.com itself, which must have SOA and NS) cannot be a CNAME. And MX and NS records must point to names with address records, not to aliases. Other types you may meet are SRV (the host and port of a service) and CAA (which certificate authorities may issue for the domain).

### A small zone file

```
$TTL 3600
example.com.  IN SOA   ns1.example.com. admin.example.com. (
                       2026100501 ; serial
                       7200       ; refresh
                       900        ; retry
                       1209600    ; expire
                       300 )      ; negative-caching TTL
example.com.  IN NS    ns1.example.com.
example.com.  IN NS    ns2.example.com.
example.com.  IN MX    10 mail.example.com.
www           IN A     203.0.113.10
www           IN AAAA  2001:db8::10
blog          IN CNAME www.example.com.
mail          IN A     203.0.113.25
ns1           IN A     203.0.113.53
ns2           IN A     198.51.100.53
```

In the SOA, admin.example.com. is the mailbox admin@example.com. Secondary servers copy the zone from the primary and use the serial to tell whether it changed; the refresh, retry and expire timers (in seconds) govern how often they check.

### Caching and TTL

Every record carries a TTL in seconds. The recursive resolver, the operating system and the browser may reuse an answer until its TTL runs out, and a cached referral lets the resolver skip the levels above it.

At 0 s the cache is empty, so looking up www.example.com takes 3 queries: root, com and example.com. The answer and both referrals are cached, each with its own TTL.

- At 0 s the cache is empty, so looking up www.example.com takes 3 queries: root, com and example.com. The answer and both referrals are cached, each with its own TTL.
- At 600 s mail.example.com is new, but the referral to example.com's servers is still cached, so the resolver goes straight there: 1 query instead of three.
- At 1,800 s www.example.com is asked again. Its A record has 1,800 of its 3,600 seconds left, so the resolver answers from memory without sending a query.
- At 4,000 s the record expired 400 seconds ago, so the resolver asks example.com's server again, still holding the referral, and the fresh answer starts a new hour.

With TTL 3600, a change to www's address can take up to an hour to reach users whose resolvers cached the old one. What people call "DNS propagation" is just caches expiring. Before moving a site to a new server, administrators lower the TTL (say, to 300 seconds) a day ahead, so the switch takes effect within minutes.

Failures are cached too: a "no such domain" answer (NXDOMAIN) is kept for the negative-caching time in the zone's SOA, so a typo does not hit the authoritative servers on every retry.

### DNS over UDP and TCP, port 53

- Queries and answers normally use UDP port 53 : one small datagram each way, no handshake. The client retries if no answer arrives.
- Classic DNS limited UDP answers to 512 bytes . A larger answer comes back truncated (the TC flag set) and the client repeats the query over TCP port 53 . The EDNS(0) extension lets UDP carry larger answers.
- Zone transfers from a primary to a secondary server (AXFR for the whole zone, IXFR for changes) use TCP port 53 .
- Encrypted variants hide queries from on-path observers: DNS over TLS (TCP 853) and DNS over HTTPS (port 443).

```
nslookup
www.example.com
# quick answer from your configured resolver
dig
www.example.com A
# full answer with TTL and header flags
dig
+trace www.example.com
# follow the referrals from the root yourself
dig
-x
203.0
.113.10
# reverse lookup (PTR)
```

Classic DNS answers are not authenticated, which allows cache poisoning : an attacker races the real answer with a forged one so the resolver caches a wrong address. Random query IDs and source ports make guessing hard, and DNSSEC lets resolvers verify records with digital signatures. See network security basics .

### Common mistakes

- Saying the root servers know every domain's address: they only refer resolvers to the TLD servers.
- Mixing up who sends which query: the stub's query is recursive, the resolver's queries are iterative.
- Saying DNS uses only UDP: TCP is used for zone transfers and truncated answers.
- Putting a CNAME at the zone apex or pointing an MX record at a CNAME.
- Thinking a DNS change "propagates" by being pushed: old answers simply live in caches until their TTL expires.
- Reading MX preference backwards: the lowest number is tried first.

### Interview questions

Walk me through what happens when a domain name is resolved. The browser and OS caches are checked first. On a miss, the stub resolver asks the recursive resolver, which asks a root server (referral to the TLD servers), a TLD server (referral to the domain's authoritative servers) and finally an authoritative server, which returns the record. Every party caches the answer for its TTL.

What is the difference between an authoritative server and a recursive resolver? An authoritative server holds the original records for a zone and answers only for that zone. A recursive resolver holds no zones of its own; it finds answers on behalf of clients by following referrals, and caches what it learns.

Why can a DNS change take hours to show up? Resolvers and clients keep cached copies of the old record until its TTL expires. If the TTL was a day, some users keep seeing the old address for up to a day. Lowering the TTL before a planned change shortens that window.

What is an MX record, and what does its preference number do? An MX record names the mail server that accepts email for a domain. A domain can list several; senders try the one with the lowest preference number first and fall back to higher numbers if it is unreachable.

When does DNS use TCP instead of UDP? For zone transfers between primary and secondary servers, and when an answer is too large for a UDP response: the server sets the truncation flag and the client repeats the query over TCP. DNS over TLS also runs on TCP.

What is a reverse DNS lookup, and where is it used? It maps an IP address back to a name through a PTR record under in-addr.arpa (ip6.arpa for IPv6). Mail servers check that a sending server's address has a sensible reverse name, and logging and diagnostic tools show names instead of numbers.

What is DNS cache poisoning, and how is it prevented? It is tricking a resolver into caching a forged record, so its users are sent to an attacker's address. Defences include randomised query IDs and source ports, which make forged replies hard to match, and DNSSEC, which signs records so resolvers can verify them.

Next, read HTTP and HTTPS , and test yourself with the Computer Networks (Basic) skill test .

### What is the difference between recursive and iterative DNS queries?

In a recursive query the server asked must return the final answer, chasing it down itself; your computer sends this kind to its resolver. In an iterative query the server replies with the best it knows, often a referral to other servers, and the asker continues; resolvers query root, TLD and authoritative servers this way.

### What is the difference between an A record and a CNAME record?

An A record maps a name directly to an IPv4 address. A CNAME record says a name is an alias for another name, so the resolver must then look up the target's A or AAAA record. A name that has a CNAME cannot have any other records, so a CNAME cannot sit at a zone's apex.

### What is TTL in DNS?

TTL (time to live) is the number of seconds a resolver may cache a record before asking again. A TTL of 3600 means an answer can be reused for up to an hour. Long TTLs cut lookup traffic and delay; short TTLs let changes, such as a new server address, take effect sooner.

### How many DNS root servers are there?

There are 13 named root server identities, a.root-servers.net to m.root-servers.net, run by 12 independent organisations. Each identity is served from many machines around the world using anycast, so the 13 names stand for far more than 13 physical servers.

### What is a reverse DNS lookup?

It finds the name for an IP address using a PTR record. The address's octets are reversed under in-addr.arpa, so 203.0.113.10 is looked up as 10.113.0.203.in-addr.arpa. Mail servers use reverse lookups to judge senders, and logs use them to show readable host names.


---

## Module 9: HTTP and HTTPS

*Original URL: https://codekairo.com/notes/computer-networks/http-and-https*

### Overview

Quick answer

### What is the difference between HTTP and HTTPS?

HTTP (Hypertext Transfer Protocol) is the stateless request-response protocol that browsers, apps and servers use to exchange web pages and API data, by default on TCP port 80. HTTPS is the same HTTP carried inside a TLS-encrypted connection, by default on port 443. TLS adds encryption, integrity checking and server authentication through certificates, so an eavesdropper on the network can neither read nor silently change the traffic.

- How HTTP works
- The request and the response
- HTTP methods
- Status codes
- Headers
- Statelessness, cookies and sessions
- HTTP/1.1 vs HTTP/2 vs HTTP/3
- HTTPS and the TLS handshake
- REST basics
- Common mistakes
- Interview questions
- Common questions
- Test yourself

HTTP is the protocol of the web: every page, image, script and API call your browser makes is an HTTP request answered by an HTTP response. It is simple on purpose (text messages in its classic form, one request and one response) and stateless, which is what lets it scale to billions of users. HTTPS is not a different protocol; it is HTTP sent through an encrypted TLS tunnel. This note covers the message format, methods, status codes, state, the three HTTP versions and the TLS handshake.

### How HTTP works

HTTP is a client-server, request-response protocol at the application layer. The client (a browser, an app, curl ) opens a connection to the server, sends a request and reads the response. HTTP/1.1 and HTTP/2 run over TCP; HTTP/3 runs over QUIC on UDP. The resource is named by a URL:

### The request and the response

A request has a request line (method, path, version), headers , a blank line and an optional body . A response has the same shape with a status line (version, status code, reason phrase) in front.

The request: a request line with the method, the path and the version, then headers one per line, then a blank line, then the body. Content-Length tells the server where the body ends: these 42 bytes.

- The request: a request line with the method, the path and the version, then headers one per line, then a blank line, then the body. Content-Length tells the server where the body ends: these 42 bytes.
- The response has the same shape with a status line in front: the version, the status code 201 and its reason phrase. Location names the user just created, and the body is 50 bytes.

Content-Length is the body's size in bytes, which is how the reader knows where the body ends. In HTTP/2 and HTTP/3 the same fields travel as binary frames, but the meaning is identical.

### HTTP methods

A method is safe if it does not change server state, and idempotent if sending it once or many times leaves the server in the same state.

Idempotence is about state, not the response: a second DELETE of the same item may return 404, but the server is in the same state as after the first. This is why clients and proxies may retry idempotent requests after a network failure but must not blindly retry a POST.

### Status codes

The pairs interviewers ask about:

- 401 vs 403 : 401 means "authenticate first"; 403 means "you are known, and still not allowed".
- 301 vs 302 : 301 is permanent (browsers and search engines remember the new URL), 302 is temporary. 307 and 308 are their counterparts that forbid changing the method , so a redirected POST stays a POST.
- 502 vs 504 : both come from a gateway or proxy; 502 means the upstream server sent an invalid response, 504 means it did not answer in time.
- 304 Not Modified : the client's cached copy is still valid, so no body is sent.

### Statelessness, cookies and sessions

HTTP itself remembers nothing between requests. To keep a user logged in, the server sends a cookie, and the browser returns it on every later request to that site.

The login request succeeds. The server stores the user under a random session ID, 4f2a9c, and sends that ID back in a Set-Cookie header; the browser files the cookie under this site.

- The login request succeeds. The server stores the user under a random session ID, 4f2a9c, and sends that ID back in a Set-Cookie header; the browser files the cookie under this site.
- Later, a completely separate request: HTTP itself remembers nothing of the login. But the browser attaches the cookie automatically to every request it sends to this site.
- The server looks the ID up, finds Asha, and answers as if the conversation had continued. A request with an unknown ID, such as session=000000, would get 401 Unauthorized.

A real Set-Cookie header also carries attributes that limit where and how the cookie travels:

```
Set-Cookie
:
session=4f2a9c; Path=/; Max-Age=86400; HttpOnly; Secure; SameSite=Lax
```

With a server-side session , as in the figure, the cookie holds only a random ID and the server keeps the user's data in memory, a database or a cache such as Redis. With token-based authentication, the client holds a signed token (such as a JWT) carrying the user's identity, and the server only verifies the signature. Sessions are easy to revoke; tokens need no lookup but are harder to cancel before they expire.

### HTTP/1.1 vs HTTP/2 vs HTTP/3

HTTP/1.1 on one connection: a request goes out only after the previous response has fully arrived, and each costs a round trip plus the server's time. The slow app.js holds up logo.png behind it; all three are in at 300 ms.

- HTTP/1.1 on one connection: a request goes out only after the previous response has fully arrived, and each costs a round trip plus the server's time. The slow app.js holds up logo.png behind it; all three are in at 300 ms.
- HTTP/2 sends all three requests at once and interleaves the responses as frames on one connection. While app.js is still being generated, the CSS and the image flow past it, and everything is in at 140 ms.

HTTP/1.0 (1996) opened a new connection for every request. HTTP/1.1 made persistent connections the default and added the mandatory Host header (so many sites can share one IP address) and chunked transfer. Its pipelining feature allowed several requests in a row, but responses had to come back in order and browsers left it switched off. HTTP/2's server push was later dropped by browsers. HTTP/3 also survives a change of network, such as Wi-Fi to mobile data, because QUIC identifies a connection by an ID rather than by IP addresses and ports.

### HTTPS and the TLS handshake

HTTPS gives three guarantees: confidentiality (nobody on the path can read the data), integrity (any change is detected) and authentication (a certificate proves the server owns the domain). TLS 1.3 sets all three up in one round trip after TCP's:

TCP first: SYN and SYN-ACK cost one round trip, so the client's clock reads 50 ms before any TLS message has been sent.

- TCP first: SYN and SYN-ACK cost one round trip, so the client's clock reads 50 ms before any TLS message has been sent.
- The client's ACK goes out with the ClientHello right behind it: the versions and ciphers it supports, its Diffie-Hellman key share and the server name it wants (SNI).
- The server answers with its own key share. Both sides can now compute the same secret, so everything after the ServerHello is encrypted: the certificate, a signature proving the server holds its private key, and Finished. That is round trip 2, at 100 ms.
- The client checks the certificate chain, dates and host name and the signature, sends its own Finished, and puts the first HTTP request on the same flight, already encrypted.
- The response's first byte arrives after 3 round trips, 150 ms. TLS 1.2 needed a second handshake round trip, so the same request took 200 ms; on a reused connection only the last round trip remains.

The two key shares are the halves of an ephemeral Diffie-Hellman exchange: each side combines its own private value with the other's share and arrives at the same shared secret , from which both derive the session keys, without the secret ever crossing the network. The certificate check is what stops an impostor: the chain must lead to a certificate authority the client trusts, the dates must be valid, the names must cover the requested host and it must not be revoked, and the CertificateVerify signature proves the server holds the matching private key. Application data then flows under a fast symmetric cipher such as AES-GCM or ChaCha20-Poly1305.

TLS 1.2 needed two round trips and also allowed RSA key exchange , where the client encrypts a secret with the server's public key. That lacks forward secrecy : anyone who later steals the server's private key can decrypt recorded traffic. TLS 1.3 removed it; every key exchange is ephemeral. Asymmetric cryptography is used only to agree keys and prove identity, because it is far slower than symmetric encryption; see network security basics .

### Worked example: round trips before the first response byte

Take a round-trip time of 50 ms and ignore DNS and server processing time.

On a reused connection only the last round trip remains, which is why keep-alive and connection reuse matter so much.

HTTPS does not hide everything: the IP addresses, the timing and size of traffic, the DNS lookup and normally the server name in the ClientHello (unless Encrypted Client Hello is used) are visible. The path, query string, headers, cookies and body are encrypted.

### REST basics

REST (Representational State Transfer) is a style for designing APIs on top of HTTP: resources are named by URLs (nouns), HTTP methods are the verbs, each request carries everything needed to process it ( stateless ), and resources are transferred as representations, usually JSON.

### Common mistakes

- Saying GET is secure because parameters are "hidden" in POST: both are readable over HTTP and both are encrypted over HTTPS; GET parameters do end up in logs and history.
- Calling PATCH idempotent by definition: only GET, HEAD, OPTIONS, PUT and DELETE (and TRACE) are.
- Treating 401 and 403 as the same.
- Saying HTTPS encrypts the domain name: DNS and SNI normally reveal it.
- Saying HTTP/2 removed head-of-line blocking completely: it remains at the TCP level; HTTP/3 removes it.
- Describing the TLS handshake as "the client encrypts the data with the server's public key": the public key authenticates and helps agree a symmetric key; the data is encrypted symmetrically.

### Interview questions

What is idempotency, and which HTTP methods are idempotent? A request is idempotent if repeating it leaves the server in the same state as sending it once. GET, HEAD, OPTIONS, PUT and DELETE are idempotent; POST is not, and PATCH is not guaranteed to be. It matters because idempotent requests can be retried safely after a timeout.

How do cookies make a stateless protocol stateful? The server sends a Set-Cookie header with an identifier, and the browser automatically includes it in every later request to that site. The server uses the identifier to look up the session, so a sequence of independent requests behaves like one logged-in conversation.

What did HTTP/2 improve over HTTP/1.1? It replaced text with binary framing and multiplexes many concurrent streams over a single TCP connection, so one slow response no longer blocks the others at the HTTP level and browsers need fewer connections. It also compresses headers with HPACK, saving bytes on repeated headers such as cookies.

Why does HTTP/3 run on UDP? TCP delivers bytes strictly in order, so a single lost packet stalls every HTTP/2 stream sharing the connection. QUIC, built on UDP, implements reliability per stream, so a loss affects only its own stream. It also merges the transport and TLS handshakes and can move a connection between networks.

Explain the TLS handshake. The client and server exchange supported versions, random numbers and Diffie-Hellman key shares, and both compute the same secret from which session keys are derived. The server proves its identity with its certificate and a signature made with the matching private key, both sides confirm the handshake with Finished messages, and the data then flows under symmetric encryption.

What does a certificate prove, and how does a browser check it? It binds a public key to a domain name, signed by a certificate authority. The browser follows the chain of signatures up to a root certificate in its trust store, checks the validity dates, checks that the certificate's names match the host and checks revocation; then the server must prove it holds the private key.

What is the difference between 502 and 504? Both are returned by a gateway, proxy or load balancer. 502 Bad Gateway means the upstream server returned an invalid or broken response; 504 Gateway Timeout means the upstream server did not respond within the proxy's time limit.

Next, read routing and routing protocols , and test yourself with the Computer Networks (Intermediate) skill test .

### What does it mean that HTTP is stateless?

Each request is handled on its own; the server keeps no memory of earlier requests from the same client as part of the protocol. Applications add state on top, usually with a cookie that carries a session ID or a signed token, which the browser sends back with every request.

### What is the difference between GET and POST?

GET reads a resource; its parameters travel in the URL's query string, and it is safe and idempotent, so it can be cached, bookmarked and retried. POST sends data in the request body to create something or trigger processing; it is neither safe nor idempotent, so repeating it may create a duplicate.

### What is the difference between 401 and 403 status codes?

401 Unauthorized means the request lacks valid authentication: the client has not proved who it is, or its credentials are wrong or expired. 403 Forbidden means the server knows who the client is, or does not need to, but refuses access anyway. Logging in can fix a 401 but not a 403.

### What is the difference between HTTP/1.1, HTTP/2 and HTTP/3?

HTTP/1.1 is text-based and handles one request at a time per TCP connection. HTTP/2 uses binary frames to multiplex many requests over one TCP connection and compresses headers. HTTP/3 runs over QUIC on UDP, so one lost packet no longer stalls every stream, and its handshake includes TLS 1.3.

### Is HTTPS slower than HTTP?

Only slightly, at connection setup: TLS 1.3 adds one round trip (TLS 1.2 added two), and resumed sessions can skip most of it. Once connected, symmetric encryption is cheap on modern processors. Browsers also allow HTTP/2 and HTTP/3 only over encrypted connections, so HTTPS sites are often faster overall.

### What is the difference between PUT and PATCH?

PUT replaces the whole resource at a URL with the body sent, and repeating it gives the same result, so it is idempotent. PATCH applies a partial change, such as updating one field; it is not guaranteed to be idempotent, because a patch like "add 1 to the counter" changes the result each time.


---

## Module 10: NAT, DHCP and Ports

*Original URL: https://codekairo.com/notes/computer-networks/nat-dhcp-and-ports*

### Overview

Quick answer

### What is NAT and why is it used?

NAT (Network Address Translation) lets many devices with private IP addresses share one or a few public addresses. A NAT router rewrites the source address, and in PAT also the source port, of every outgoing packet and records the change in a translation table, so replies can be sent back to the right device. It conserves scarce IPv4 addresses and hides the inside network's layout.

- Port numbers
- Sockets
- NAT: network address translation
- DHCP: Dynamic Host Configuration Protocol
- APIPA: when DHCP fails
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Three everyday mechanisms sit between an IP address and a working application. Port numbers tell a host which program a packet is for. DHCP hands a new device its address, gateway and DNS servers the moment it joins a network. NAT lets a whole home or office share one public IPv4 address. All three appear in every "how does the internet work" interview and in any real troubleshooting session, so this note works through each with concrete numbers.

### Port numbers

An IP address identifies a host; a port number (16 bits, 0 to 65,535) identifies a process on that host. Servers listen on fixed, published ports so clients know where to connect; clients use a temporary ephemeral port chosen by their operating system for each connection.

Port numbers are 16 bits, 0 to 65,535. The well-known ports are only the first 1,024; registered ports take 48,128 and IANA's dynamic range the last 16,384. Linux picks client ports from its own range, which starts inside the registered block.

### The ports worth memorising

The last five are registered rather than well-known ports, listed because they come up constantly in backend and placement interviews.

### Sockets

A socket is an endpoint: protocol plus IP address plus port. A TCP connection is identified by its two endpoints, the 4-tuple (source IP, source port, destination IP, destination port), or the 5-tuple if the protocol is counted. That is why one server port can carry thousands of connections: every client brings a different address or source port.

The server side of a TCP socket in C (display only):

```
int
fd
=
socket
(
AF_INET
,
SOCK_STREAM
,
0
)
;
/* a TCP socket */
struct
sockaddr_in
addr
=
{
0
}
;
addr
.
sin_family
=
AF_INET
;
addr
.
sin_port
=
htons
(
8080
)
;
/* port in network byte order */
addr
.
sin_addr
.
s_addr
=
htonl
(
INADDR_ANY
)
;
/* every local interface */
bind
(
fd
,
(
struct
sockaddr
*
)
&
addr
,
sizeof
addr
)
;
/* claim port 8080 */
listen
(
fd
,
16
)
;
/* queue up to 16 pending connections */
int
conn
=
accept
(
fd
,
NULL
,
NULL
)
;
/* a new socket for this client */
```

The client calls socket and then connect with the server's address and port; its operating system picks the ephemeral source port. accept returns a new socket for each client:

All three connections use the server's port 8080, yet no two share a 4-tuple. The second differs from the first only in its client port, the third only in its client address (highlighted), and the listening socket keeps waiting for more.

### NAT: network address translation

IPv4 has about 4.3 billion addresses, far fewer than the devices that use them. NAT lets an entire private network (addresses from 10.0.0.0/8, 172.16.0.0/12 or 192.168.0.0/16, see IP addressing ) reach the internet through one public address. The NAT router rewrites addresses on the way out, remembers each rewrite, and reverses it for the replies.

### Worked example: a PAT translation table

A home network uses 192.168.1.0/24 and the router's public address is 203.0.113.5. Three connections leave the network:

Two laptops happened to pick the same source port, 51000, for the same server; the router gives them different public ports, so their replies cannot be confused. A reply for 203.0.113.5:40002 goes back to 192.168.1.11:51000 , and a packet that matches no entry is dropped :

192.168.1.10 opens a connection from port 51000. The router rewrites the private source to its public address and a fresh port, 40001, and records the pair in its translation table.

- 192.168.1.10 opens a connection from port 51000. The router rewrites the private source to its public address and a fresh port, 40001, and records the pair in its translation table.
- 192.168.1.11 happens to pick the same source port, 51000, for the same server. Its packets get their own public port, 40002, so the two connections stay apart outside.
- A second connection from 192.168.1.10, to another server, gets public port 40003. Every connection is one row; the destination is never rewritten on the way out.
- A reply from 198.51.100.20:443 arrives for 203.0.113.5:40002. The router finds port 40002 in its table, rewrites the destination to 192.168.1.11:51000 and forwards it inside.
- A packet for 203.0.113.5:50000 matches no row: nobody inside asked for it, so there is nowhere to send it and it is dropped. This is why a server behind NAT needs a port-forwarding entry.

How the public port is chosen varies by router: many keep the original port when it is free. Every rewrite also means updating the IP header checksum and the TCP or UDP checksum, because both cover the addresses.

Port forwarding is a static entry added by hand so that inbound traffic works: "send anything arriving on public port 8443 to 192.168.1.50:443" lets a server inside be reached from outside.

### What NAT breaks

- End-to-end reachability : hosts behind NAT cannot accept unsolicited connections without port forwarding. Peer-to-peer applications and video calls use NAT traversal tricks (STUN, hole punching, or relaying through TURN servers).
- Protocols that carry addresses inside their data , such as active-mode FTP and SIP, need an application layer gateway in the router to rewrite those too.
- State : the router keeps an entry per connection and silently drops idle ones after a timeout.
- Attribution : with carrier-grade NAT, thousands of customers share one ISP address, so a public address alone no longer identifies a user.

IPv6 has enough addresses that NAT is unnecessary; firewalls, not address translation, then provide the protection.

### DHCP: Dynamic Host Configuration Protocol

DHCP gives a device everything it needs to join an IP network: an IP address , the subnet mask , the default gateway , the DNS servers and a lease time , plus optional settings such as the domain name. It runs over UDP, servers on port 67 and clients on port 68.

### The DORA exchange

A laptop with no address joins a network. Here two servers answer, which shows why the third message is a broadcast even though the client already knows which server it wants:

Discover: the laptop has no address yet, so it broadcasts from 0.0.0.0 port 68 to 255.255.255.255 port 67, with its MAC address inside. Every DHCP server on the segment hears it.

- Discover: the laptop has no address yet, so it broadcasts from 0.0.0.0 port 68 to 255.255.255.255 port 67, with its MAC address inside. Every DHCP server on the segment hears it.
- Offer: each server reserves an address from its pool and offers it with the mask, gateway, DNS servers and lease time. Server A offers 192.168.1.23, server B 192.168.1.150.
- Request: the laptop takes A's offer and broadcasts its choice, naming server A. Broadcasting is the point: server B hears that its offer was declined and returns 192.168.1.150 to its pool.
- Acknowledge: server A confirms the lease. After an optional ARP probe to make sure nobody else uses it, the laptop configures 192.168.1.23 and its settings for the lease time.

Server A's offer carried the address 192.168.1.23 with mask 255.255.255.0, gateway 192.168.1.1, DNS servers and a 24-hour lease. If the client's ARP probe of the offered address gets an answer, the address is already in use: it sends DHCPDECLINE and starts again.

Leases and renewal. At T1, by default half the lease, the client sends a unicast DHCPREQUEST to its server to renew. If that fails, at T2, by default 87.5 per cent, it broadcasts the request to any server (rebinding). If the lease expires, it must stop using the address. For a 24-hour lease, T1 falls at 12 hours and T2 at 21 hours.

For a 24-hour lease, the client starts renewing with its own server at T1 = 12 hours. If that server stays silent, at T2 = 21 hours it broadcasts to any server; if the lease ends with no answer, it must give the address up.

Relay agents. Broadcasts do not cross routers, so a network with one central DHCP server needs a relay agent on each subnet's router (on Cisco, the ip helper-address command). The relay forwards the client's broadcasts to the server as unicast and records its own interface address, which tells the server which subnet's pool to allocate from.

### APIPA: when DHCP fails

If no DHCP server answers, Windows and many other systems give themselves a link-local address from 169.254.0.0/16 (the usable range is 169.254.1.0 to 169.254.254.255), after checking with ARP that no neighbour already uses it. This is APIPA (Automatic Private IP Addressing). The host can talk to other link-local hosts on the same network segment but has no gateway, so it cannot reach the internet, and it keeps retrying DHCP in the background. In troubleshooting, a 169.254 address almost always means "the DHCP server is unreachable".

### Common mistakes

- Swapping DHCP's ports: the server listens on 67 and the client on 68.
- Saying the DHCP Request is unicast during DORA: it is broadcast, so the other servers can withdraw their offers.
- Treating NAT as a firewall feature by design: dropping unsolicited packets is a side effect of having no table entry, not a security policy.
- Saying a server needs a new port per client: every connection shares the listening port and differs in the client's address or port.
- Thinking APIPA hosts can reach the internet: they have no gateway and are limited to the local link.
- Calling 3306 or 8080 well-known ports: they are registered ports.

### Interview questions

What is the difference between a port and a socket? A port is just a 16-bit number identifying a service on a host. A socket is a full endpoint, an IP address plus a port for a given protocol, and a TCP connection is defined by the pair of sockets at its two ends.

How does PAT let fifty devices share one public IP address? The router rewrites each outgoing packet's private source address and port to its public address and a unique public port, and stores the mapping. Replies arrive at that public port, and the router uses the table to restore the original private address and port.

Why is the DHCP Request message broadcast? Several servers may have made offers and reserved addresses for the client. Broadcasting the request, with the chosen server's identifier in it, tells every server at once which offer was accepted, so the others can return their reserved addresses to the pool.

How does a host on a subnet without a DHCP server still get an address? A DHCP relay agent, usually configured on the subnet's router, picks up the client's broadcasts and forwards them as unicast to the central server. It adds its own interface address so the server allocates from the right subnet's pool.

What happens when a DHCP lease expires? Before that point the client tries to renew at T1 (half the lease) with its own server and at T2 (87.5 per cent) with any server. If neither succeeds before expiry, the client must stop using the address and start again with a Discover.

Can two programs listen on the same port at the same time? Normally no: binding a second socket to the same protocol, address and port fails with "address already in use". TCP port 53 and UDP port 53 are different sockets, so a DNS server uses both, and options such as Linux's SO_REUSEPORT let cooperating processes share one port.

Why does NAT cause trouble for peer-to-peer applications? Each peer is behind its own NAT with no public port open for unsolicited packets, so neither can simply connect to the other. Applications learn their public address and port with STUN, try to open matching mappings from both sides at once (hole punching), and fall back to relaying through a TURN server.

Next, read what happens when you type a URL , and test yourself with the Computer Networks (Basic) skill test .

### What are well-known port numbers?

Ports 0 to 1023 are the well-known ports, assigned by IANA to standard services: 22 for SSH, 25 for SMTP, 53 for DNS, 80 for HTTP and 443 for HTTPS, among others. On Unix-like systems a program usually needs administrator rights to listen on one of them.

### What is the difference between NAT and PAT?

Basic NAT maps private addresses to public addresses one to one, so it needs as many public addresses as there are simultaneous inside hosts. PAT (port address translation, also called NAPT or NAT overload) maps many private addresses to one public address and tells the connections apart by giving each its own public port.

### What is the DORA process in DHCP?

DORA is the four-message exchange by which a client gets an address: Discover (the client broadcasts to find servers), Offer (a server proposes an address and settings), Request (the client broadcasts which offer it accepts) and Acknowledge (the server confirms the lease). The client then configures the address for the lease time.

### Which ports does DHCP use?

DHCP runs over UDP. Servers listen on port 67 and clients on port 68. A client with no address yet sends from 0.0.0.0 port 68 to the broadcast address 255.255.255.255 port 67.

### What is a socket in networking?

A socket is one endpoint of a network conversation, identified by an IP address and a port number together with the protocol. A TCP connection is the pair of sockets at its two ends, so it is uniquely identified by source address, source port, destination address and destination port.

### What does a 169.254.x.x IP address mean?

It is a link-local address the device gave itself through APIPA because no DHCP server answered. It can talk only to other devices on the same local link that also use such addresses and has no default gateway, so seeing it usually means DHCP has failed.


---

## Module 11: Network Security Basics

*Original URL: https://codekairo.com/notes/computer-networks/network-security-basics*

### Overview

Quick answer

### What is network security?

Network security is the set of protocols, devices and practices that protect data and systems on a network from unauthorised access, alteration and disruption. Its goals are the CIA triad: confidentiality, integrity and availability. The main tools are encryption (symmetric, such as AES, and asymmetric, such as RSA), hashing, digital signatures and certificates, firewalls and VPNs, together with defences against attacks such as man-in-the-middle and DDoS.

- The CIA triad
- Symmetric encryption
- Asymmetric (public-key) encryption
- Hashing
- Digital signatures and certificates
- Firewalls
- VPNs
- Common attacks and defences
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Every protocol in the earlier notes was designed for a network of trusted researchers: IP does not check source addresses, ARP believes any reply, and classic DNS and HTTP send everything in clear text. Network security adds what those protocols lack. Cryptography keeps data secret and tamper-evident, certificates prove who is on the other end, firewalls and VPNs control what may cross a boundary, and specific defences blunt specific attacks.

### The CIA triad

Three more terms are often added: authentication (proving who you are), authorisation (what you are allowed to do) and non-repudiation (a sender cannot later deny sending a message, provided by digital signatures).

### Symmetric encryption

One shared secret key both encrypts and decrypts. It is fast, often built into processor hardware, so it encrypts all bulk data. AES (block size 128 bits, keys of 128, 192 or 256 bits) is the standard; ChaCha20 is a fast alternative in software. DES , with its 56-bit key, can be brute-forced and is broken, and 3DES is deprecated.

Its weakness is key distribution : the two parties must already share the key secretly, and every pair of people needs its own key, n(n − 1)/2 of them for n people.

### Asymmetric (public-key) encryption

Each party has a key pair . The public key can be published; the private key never leaves its owner. What one key does, only the other can undo:

- encrypt with the recipient's public key, and only the recipient's private key can decrypt (confidentiality);
- sign with your private key, and anyone can verify with your public key (authenticity).

Symmetric: Alice and Bob share one secret key. A toy XOR cipher turns 0100 into 1111 and the same key turns it back. Fast, but the key had to reach Bob secretly first.

- Symmetric: Alice and Bob share one secret key. A toy XOR cipher turns 0100 into 1111 and the same key turns it back. Fast, but the key had to reach Bob secretly first.
- Asymmetric: Alice encrypts with Bob's public key, 4^3 mod 33 = 31. Only Bob's private key undoes it: 31^7 mod 33 = 4. The public key could have been printed in a newspaper.

RSA , whose security rests on the difficulty of factoring a large number, and elliptic-curve algorithms (ECDH, ECDSA) are the common families. They are far slower than symmetric ciphers, so they are used for small jobs: agreeing keys and signing.

### Worked example: toy RSA

Real RSA uses primes hundreds of digits long; small numbers show the mechanics.

Anyone may know (3, 33), but finding d = 7 requires φ(33), which requires factoring 33. For a 2,048-bit n, no known method can factor it in practice.

### Worked example: Diffie-Hellman key agreement

Diffie-Hellman lets two parties agree a secret over an open channel without ever sending it. Public values: prime p = 23, generator g = 5.

Alice and Bob agree in public on a prime p = 23 and a generator g = 5. Anyone listening, Eve included, knows both.

- Alice and Bob agree in public on a prime p = 23 and a generator g = 5. Anyone listening, Eve included, knows both.
- Each picks a private number and never sends it: Alice 6, Bob 15. Each raises g to it: Alice gets 5^6 mod 23 = 8, Bob 5^15 mod 23 = 19.
- They swap A = 8 and B = 19 in the open. Eve now holds 23, 5, 8 and 19, but turning 8 back into 6 means solving a discrete logarithm, which is infeasible for real key sizes.
- Alice computes 19^6 mod 23 = 2 and Bob 8^15 mod 23 = 2: the same number, since both equal 5^(6 × 15) mod 23. The shared secret 2 never crossed the network.

TLS 1.3 uses the elliptic-curve version with fresh numbers for every connection (ephemeral keys), which gives forward secrecy .

### Symmetric vs asymmetric

With symmetric keys every pair of the 5 people needs its own secret: n(n − 1)/2 = 10. With key pairs each person needs one, 10 keys in all. At 100 people that is 4,950 shared keys against 200.

Real systems are hybrid : TLS uses asymmetric cryptography to authenticate the server and agree a key, then encrypts the data with a symmetric cipher such as AES-GCM ( HTTP and HTTPS ).

### Hashing

A cryptographic hash function turns any input into a fixed-size digest . SHA-256 always outputs 256 bits (64 hexadecimal characters). A good hash is deterministic and fast, and it is:

- preimage resistant : given a digest, you cannot find an input that produces it;
- second-preimage resistant : given an input, you cannot find another with the same digest;
- collision resistant : you cannot find any two inputs with the same digest;
- sensitive to change: flipping one input bit changes about half the output bits (the avalanche effect).

MD5 and SHA-1 have practical collision attacks and must not be used for security; SHA-256 and SHA-3 are current. Passwords are stored as the output of a deliberately slow, salted function such as bcrypt, scrypt or Argon2: the random salt per user means identical passwords get different hashes and precomputed tables are useless. An HMAC mixes a secret key into a hash, so the receiver can check both integrity and that the sender knew the key.

### Digital signatures and certificates

A digital signature is a value computed over the message's hash with the sender's private key , which anyone can check with the sender's public key :

The sender hashes "PAY 50" to 4 and raises it to the private exponent: 4^7 mod 33 = 16. The signature travels with the message, which stays perfectly readable.

- The sender hashes "PAY 50" to 4 and raises it to the private exponent: 4^7 mod 33 = 16. The signature travels with the message, which stays perfectly readable.
- The receiver hashes the message itself and raises the signature to the public exponent: 16^3 mod 33 = 4. The two match, so the message is unchanged and only the private key's holder could have signed it.
- Change the message to "PAY 90" on the way and its hash becomes 8, while the signature still opens to 4. They differ, so the forgery is caught; making a new signature would need the private key.

A valid signature proves integrity (any change breaks it), authenticity (only the private key holder could make it) and non-repudiation . It does not hide the message.

But how do you know a public key really belongs to example.com? A digital certificate (X.509) binds a public key to a name, and a certificate authority (CA) signs it. Browsers and operating systems ship a trust store of root CA certificates; a site's certificate is signed by an intermediate CA , which is signed by a root, forming a chain of trust . A client checks each signature up the chain, the validity dates, that the certificate's names include the host, and that it is not revoked (through CRLs or OCSP).

### Firewalls

A firewall enforces rules about what traffic may cross a boundary.

Next-generation firewalls combine stateful filtering with application identification and intrusion prevention, and a web application firewall (WAF) sits in front of a website to block attacks such as SQL injection and cross-site scripting. Rules are checked top to bottom and the first match wins:

HTTPS to the web server from anywhere: rule 1 matches at once and the packet is allowed. The rules below it are never looked at.

- HTTPS to the web server from anywhere: rule 1 matches at once and the packet is allowed. The rules below it are never looked at.
- SSH from 10.4.2.9, an internal address: rule 1 (wrong port) does not match, but rule 2 does, because 10.4.2.9 is inside 10.0.0.0/8. Allowed.
- SSH from outside, 198.51.100.7: rule 1 (wrong port) and rule 2 (wrong source) do not match, so it falls through to rule 3, the default deny. Dropped.

### VPNs

A virtual private network carries traffic through an encrypted tunnel across an untrusted network, so a remote laptop ( remote-access VPN ) or a whole branch office ( site-to-site VPN ) behaves as if it were on the private network. Common protocols are IPsec at the network layer, TLS-based VPNs, and WireGuard. IPsec's ESP protocol provides encryption and integrity (its AH protocol provides integrity only), in transport mode , which protects the payload of the original packet, or tunnel mode , which wraps the entire original packet inside a new one, as gateways do. A VPN hides traffic from the local network and the ISP, but the VPN operator can see it, and it does not stop malware or phishing.

### Common attacks and defences

The attack that certificates exist to defeat is the man in the middle :

After ARP spoofing on the local network, the client's packets for example.com reach the attacker first. The attacker accepts the connection, hoping to sit in the middle and read everything.

- After ARP spoofing on the local network, the client's packets for example.com reach the attacker first. The attacker accepts the connection, hoping to sit in the middle and read everything.
- To relay, the attacker opens its own connection to the real server and gets the real certificate. It cannot reuse that certificate towards the client: it lacks the matching private key to sign the handshake.
- So it presents a certificate for example.com that it made itself, signed by its own CA. The client finds no chain from that issuer to any root in its trust store, so the check fails and it aborts before sending any data.

The SYN flood and SYN cookies are explained in TCP and UDP , and DNS cache poisoning in DNS .

### Common mistakes

- Saying hashing is encryption: a hash cannot be decrypted; it is one-way.
- Saying a digital signature encrypts the message: it proves who sent it and that it is unchanged, but the message stays readable.
- Mixing up which key does what: encrypt with the recipient's public key; sign with your own private key.
- Treating Base64 as security: it is encoding, reversible by anyone.
- Storing passwords with plain SHA-256: use a salted, deliberately slow function such as bcrypt or Argon2.
- Believing HTTPS or a VPN stops phishing: they protect the channel, not a user who types a password into the wrong site.

### Interview questions

Why does TLS use both asymmetric and symmetric encryption? Asymmetric cryptography solves key distribution and proves identity, but it is far too slow for bulk data. So TLS uses it only to authenticate the server and agree a shared key, then encrypts the actual traffic with a fast symmetric cipher such as AES.

How many keys do 100 users need with symmetric and with asymmetric encryption? Symmetric: one per pair, 100 × 99 / 2 = 4,950 keys. Asymmetric: one key pair per user, 200 keys, since anyone can encrypt to a user with that user's single public key.

Why should passwords be hashed with a salt rather than encrypted? A server never needs to recover a password, only to check one, so a one-way hash is enough, and there is no decryption key to steal. A unique random salt makes identical passwords hash differently and defeats precomputed tables, and a slow function makes guessing expensive.

How does a digital signature provide non-repudiation? Only the holder of the private key could have produced a signature that the matching public key verifies. If the public key is bound to a person or company by a certificate, the signer cannot credibly deny having signed, unless the private key was stolen.

What is the difference between a stateless and a stateful firewall? A stateless firewall judges every packet alone by its header fields, so replies need their own broad rules. A stateful firewall tracks connections, automatically allows the replies to connections started from inside, and drops packets that belong to no known connection.

How does HTTPS stop a man-in-the-middle attack? The attacker can intercept the connection but cannot present a valid certificate for the real domain signed by a trusted CA, nor sign the handshake with the real server's private key. The browser's certificate check fails and it refuses to continue. Users clicking through certificate warnings is how such attacks still succeed.

What is a DDoS amplification attack? The attacker sends small requests to open servers, such as DNS resolvers, with the victim's address forged as the source. The servers send much larger replies to the victim, multiplying the attacker's bandwidth. Defences include ISPs filtering spoofed source addresses, closing open resolvers and absorbing traffic with large scrubbing networks.

What is the difference between IPsec transport mode and tunnel mode? Transport mode protects only the payload and keeps the original IP header, used between two hosts. Tunnel mode encrypts the whole original packet, header included, and puts it inside a new packet between two gateways, which is how site-to-site VPNs work.

That completes the Computer Networks notes . Test yourself with the Computer Networks (Basic) skill test , then the Computer Networks (Intermediate) skill test .

### What is the CIA triad in network security?

The CIA triad names the three goals of security. Confidentiality means only authorised parties can read the data, integrity means the data cannot be changed without detection, and availability means systems and data are reachable when needed. Encryption serves confidentiality, hashes and signatures serve integrity, and redundancy and DDoS protection serve availability.

### What is the difference between symmetric and asymmetric encryption?

Symmetric encryption uses one shared secret key to encrypt and decrypt; it is fast, as in AES, but the key must be shared secretly first. Asymmetric encryption uses a key pair: a public key anyone may hold and a private key only its owner keeps. It is much slower, so it is used for key exchange and signatures, as in RSA.

### What is the difference between encryption and hashing?

Encryption is reversible: with the right key, the ciphertext turns back into the original data, so it protects confidentiality. Hashing is one-way: it turns any input into a fixed-size digest that cannot be reversed, so it is used to check integrity and to store passwords. Encoding, such as Base64, is neither; anyone can reverse it.

### What is a firewall?

A firewall is a device or program that allows or blocks traffic between networks according to rules. Packet-filtering firewalls check each packet's addresses, protocol and ports; stateful firewalls also track connections, so replies are allowed automatically; application-level firewalls inspect the content of protocols such as HTTP.

### What is a man-in-the-middle attack?

In a man-in-the-middle attack, the attacker secretly sits between two parties, relaying and possibly altering their messages while each believes it is talking to the other. ARP spoofing on a local network and fake Wi-Fi hotspots are common ways in. TLS with proper certificate checks defeats it, because the attacker cannot prove to be the real server.

### What is the difference between DoS and DDoS attacks?

A denial-of-service attack tries to make a service unavailable by exhausting its bandwidth, connections or processing. A DoS comes from one source, which can be blocked. A distributed DoS comes from thousands of machines at once, often a botnet, so blocking single addresses does not work and large-scale filtering is needed.


---

## Module 12: What Happens When You Type a URL

*Original URL: https://codekairo.com/notes/computer-networks/what-happens-when-you-type-a-url*

### Overview

Quick answer

### What happens when you type a URL into a browser and press Enter?

The browser parses the URL, checks its caches and resolves the host name to an IP address with DNS. It opens a TCP connection with the three-way handshake, negotiates TLS for HTTPS and sends an HTTP GET request, which routers forward hop by hop to the server or a CDN edge. The server sends back HTML, and the browser parses it, fetches the page's other resources, then lays out and paints the page.

- The short answer
- Step 1: parsing the URL
- Step 2: checking the caches
- Step 3: DNS resolution
- Step 4: getting the first packet out
- Step 5: the TCP handshake
- Step 6: the TLS handshake
- Step 7: the HTTP request
- Step 8: across the internet
- Step 9: on the server side
- Step 10: rendering the page
- Keep-alive and closing
- Worked example: the timeline of a first visit
- Which protocol does what
- Common mistakes
- Interview questions
- Common questions
- Test yourself

"What happens when you type a URL and press Enter?" is the classic networking interview question because it touches every layer at once: name resolution, addressing, the transport handshake, encryption, routing, the application protocol and finally the browser. A good answer is ordered, names the protocol at each step and can go deeper wherever the interviewer pushes. This note gives the thirty-second version first, then each step in detail, with links to the notes that cover each protocol in full.

### The short answer

- The browser parses what you typed into a URL: scheme, host, port, path.
- It checks its caches : the page itself, an open connection to the site, the DNS answer.
- DNS resolves the host name to an IP address.
- The operating system finds the default gateway's MAC address with ARP , and the home router applies NAT .
- A TCP connection opens with the three-way handshake (port 443).
- A TLS handshake agrees keys and checks the server's certificate.
- The browser sends an HTTP GET request .
- Routers forward the packets hop by hop across the internet to the server or a CDN edge.
- The server side (CDN, load balancer, web server, application, database) builds the response.
- The browser receives the HTML , fetches the CSS, scripts and images it references, and renders the page.

### Step 1: parsing the URL

The browser first decides whether you typed an address or a search: "example.com" looks like a host, "tcp vs udp" does not and goes to the default search engine. A URL such as https://www.example.com/products?id=7 splits into the scheme ( https , hence default port 443), the host ( www.example.com ), the path ( /products ) and the query ( id=7 ). If you typed no scheme, many modern browsers try HTTPS first. If the host is on the browser's HSTS list (built in, or remembered from a Strict-Transport-Security header on an earlier visit), the browser upgrades to HTTPS before a single packet leaves.

### Step 2: checking the caches

- HTTP cache. If the page is cached and still fresh under its Cache-Control rules, the browser can show it with no network traffic at all. If it is stale but has an ETag , the browser sends a conditional request and may get a short 304 Not Modified .
- Connection reuse. If the browser already holds an open connection to this origin, it reuses it and skips DNS, TCP and TLS entirely.
- DNS caches. The browser's cache, the operating system's cache and the hosts file are checked before any query is sent.

### Step 3: DNS resolution

On a miss, the operating system's stub resolver asks the configured recursive resolver (learned from DHCP) over UDP port 53. If that resolver has nothing cached, it asks a root server, then the .com TLD servers, then example.com 's authoritative server, caches the answer for its TTL and returns, say, 203.0.113.10. The full walk-through is in DNS . The browser may receive both an IPv4 (A) and an IPv6 (AAAA) address and try both.

### Step 4: getting the first packet out

The host compares 203.0.113.10 with its own address and subnet mask and sees that it is on another network, so the packet must go to the default gateway . The host needs the gateway's MAC address; if it is not in the ARP cache, it broadcasts an ARP request and the router answers ( data link layer ). On Wi-Fi the frame first goes to the access point, under CSMA/CA. The home router then performs NAT , recording each rewrite so the replies can find their way back ( NAT, DHCP and ports ):

The server is on another network, so the Ethernet frame is addressed to the home router's MAC address (found by ARP), while the IP packet inside is addressed to the server itself.

- The server is on another network, so the Ethernet frame is addressed to the home router's MAC address (found by ARP), while the IP packet inside is addressed to the server itself.
- The home router rebuilds the frame for its next link with new MAC addresses, lowers the TTL to 63, and its NAT rewrites the private source to 203.0.113.5, port 40001. These 5 fields change.
- At the ISP's router only the frame and the TTL change: new MAC addresses for the next link, TTL 62. The IP addresses and ports now stay fixed all the way to the server.

### Step 5: the TCP handshake

The browser opens a TCP connection to 203.0.113.10 port 443 from an ephemeral port: SYN, SYN-ACK, ACK. Both sides now know each other's initial sequence numbers and receive windows, at the cost of one round trip ( TCP and UDP ). With HTTP/3 this step and the next merge into a single QUIC handshake over UDP.

### Step 6: the TLS handshake

In TLS 1.3, the ClientHello carries supported cipher suites, a key share and the server name (SNI); the ServerHello returns the server's key share, its certificate and a signature proving it holds the certificate's private key. The browser checks that the certificate chains to a trusted authority, is in date, matches www.example.com and is not revoked. Both sides derive the same symmetric keys, one round trip after the TCP handshake ( HTTP and HTTPS ). A certificate error stops the browser here with a warning page.

### Step 7: the HTTP request

```
GET
/products?id=7
HTTP/1.1
Host
:
www.example.com
User-Agent
:
Mozilla/5.0
Accept
:
text/html
Accept-Encoding
:
gzip, br
Cookie
:
session=4f2a9c
```

Over HTTP/2 or HTTP/3 the same fields travel as compressed binary frames on a stream, and later requests for the page's resources are multiplexed on the same connection.

### Step 8: across the internet

The request is split into IP packets. Every router on the way decrements the packet's TTL, looks up the destination with longest prefix match and forwards it to the next hop, rebuilding the frame for the next link as in the figure above; between ISPs, the routes were chosen by BGP ( routing ). traceroute shows these hops.

### Step 9: on the server side

DNS may have pointed the browser at a CDN edge near you rather than the origin. Behind it, a load balancer picks one of many servers and often terminates TLS; a reverse proxy or web server (such as Nginx) serves static files and passes dynamic requests to the application server , which reads from a cache or a database and builds the HTML or JSON.

DNS pointed the browser at a nearby CDN edge, not the origin. The logo is in the edge's cache, so the edge answers at once and nothing behind it hears about the request.

- DNS pointed the browser at a nearby CDN edge, not the origin. The logo is in the edge's cache, so the edge answers at once and nothing behind it hears about the request.
- The product page is dynamic: the edge passes it on. TLS ends at the load balancer, which picks a server; the app server misses in the cache for product 7 and reads the database, and the HTML returns the same way.

The response comes back with a status line (200 OK, or a 301 redirect that starts another request), headers such as Content-Type , Cache-Control and Set-Cookie , and a body, usually compressed with gzip or Brotli.

### Step 10: rendering the page

The browser parses the HTML into the DOM and the CSS into the CSSOM ; together they give the render tree of what is visible, which is laid out, painted and composited:

The HTML parser turns the markup into the DOM, a tree of element nodes, while the bytes are still arriving. Every element is in it, the head and the hidden promotion included.

- The HTML parser turns the markup into the DOM, a tree of element nodes, while the bytes are still arriving. Every element is in it, the head and the hidden promotion included.
- The CSS is parsed into the CSSOM, a set of rules the browser matches against every DOM node. Here two rules hide things and two set font sizes.
- DOM plus CSSOM gives the render tree: only what will be drawn. Rules with display: none drop head and p.promo and everything inside them, so the title and "Sale" never reach the screen.
- Layout computes each box's position and size: the 32 px heading takes 40 px from the top, and the paragraph starts at y 40. Change a size or add text and this step, a reflow, runs again.
- Paint fills each box with pixels, text, colours and borders, and compositing stacks the painted layers on screen. Only now does the visitor see the page.

On finding stylesheets, scripts and images, the parser requests them, reusing the connection. Ordinary scripts pause HTML parsing while they download and run, which is why pages mark them defer or async . JavaScript may then call APIs for more data and change the page.

### Keep-alive and closing

The connection is not closed after the page: HTTP/1.1 keeps it alive by default and HTTP/2 multiplexes everything over it, so the next click skips DNS, TCP and TLS. After an idle timeout, either side closes it with a TCP FIN exchange.

### Worked example: the timeline of a first visit

Assume the recursive resolver already has the name cached and is 10 ms away (round trip), the server is 40 ms away (round trip), the server needs 50 ms to build the page, TLS 1.3 is used and transmission time is negligible.

DNS first: there is nothing to connect to until the name is an address. The recursive resolver, 10 ms away, has www.example.com cached and answers 203.0.113.10.

- DNS first: there is nothing to connect to until the name is an address. The recursive resolver, 10 ms away, has www.example.com cached and answers 203.0.113.10.
- The TCP handshake with the server, 40 ms away: SYN out, SYN-ACK back. The browser's ACK will ride with its next message, so the clock reads 50 ms.
- TLS 1.3 needs one more round trip: key shares, the certificate and Finished. 90 ms have passed and not one byte of the page has been asked for.
- The GET goes out, the server spends 50 ms building the page, and the first byte of HTML arrives at 180 ms — before any CSS or image. Over QUIC it would be 140 ms; on a reused connection, 90 ms.

The first byte of HTML arrives after about 180 ms , before any CSS or images. With HTTP/3, QUIC folds the TCP and TLS round trips into one, giving 10 + 40 + 90 = 140 ms . On a repeat visit over a kept-alive connection, only the last row remains: 90 ms . This is why CDNs (shorter round trips), connection reuse and caching matter more for page speed than raw bandwidth.

### Common mistakes

- Skipping DNS, or putting it after the TCP handshake: there is nothing to connect to until the name is resolved.
- Saying the laptop ARPs for the web server: for an off-subnet destination it ARPs for its default gateway.
- Putting TLS before TCP for HTTPS over TCP: TCP connects first, then TLS runs inside it (only QUIC merges them).
- Saying the destination IP address changes at every router: only the MAC addresses change, plus NAT at the edge.
- Forgetting redirects: a 301 to the HTTPS or www address costs another full request.
- Ending at "the server sends HTML": the browser still fetches subresources and renders.

### Interview questions

Why must DNS happen before the TCP handshake? TCP connects to an IP address and port, not to a name. Until DNS has turned www.example.com into an address, the operating system has nowhere to send the SYN.

Which MAC address does the first frame from your laptop carry? The default gateway's. The destination is on another network, so the laptop sends the frame to its router, found through ARP, while the IP packet inside is addressed to the web server.

What does the browser check during the TLS handshake? That the server's certificate chains to a trusted certificate authority, is within its validity period, names the requested host and is not revoked, and that the server proved possession of the matching private key by signing the handshake. Any failure produces a certificate warning.

How does a CDN make this faster? It shortens the distance for every round trip: DNS or anycast directs the browser to a nearby edge, so the TCP, TLS and HTTP exchanges cover tens of kilometres rather than thousands, and cached content is served without contacting the origin at all.

What happens if you type http:// for a site that uses HSTS? If the browser has seen the site's HSTS header before, or the site is on the built-in preload list, it rewrites the URL to https:// internally and never sends the plain HTTP request, which prevents an attacker on the network from intercepting that first request.

How are the images and scripts on a page fetched? As the HTML parser finds references to them, the browser issues more HTTP requests, normally to the same or a few other origins. Over HTTP/2 or HTTP/3 they are multiplexed as parallel streams on one connection; HTTP/1.1 browsers open several connections per host instead.

How would you debug a page that will not load? Work up the layers: check the device has an address (not 169.254), ping the gateway, resolve the name with nslookup or dig , test reachability with ping and traceroute , then fetch with curl -v to see the TLS handshake and the HTTP status. Browser developer tools show the timing of every request.

Next, read network security basics , and test the whole path with the Computer Networks (Basic) skill test .

### Which protocols are used when you open a website?

DNS finds the server's IP address, ARP finds the local gateway's MAC address, TCP (or QUIC over UDP) carries the connection, TLS encrypts it, and HTTP fetches the content. Underneath, IP routes the packets across networks and Ethernet or Wi-Fi carries them over each link; DHCP gave your device its address when it joined the network.

### Why does a website load faster the second time?

Much of the work is cached. The DNS answer is reused until its TTL expires, the browser may still hold an open connection so the TCP and TLS handshakes are skipped, and images, scripts and stylesheets come from the HTTP cache. Only what changed, or what the cache rules require checking, travels over the network.

### Does the browser contact the website's server directly?

Often not. Many sites sit behind a content delivery network, so DNS returns the address of a nearby CDN edge server, which answers from its cache or fetches from the origin server. Inside the provider, load balancers and reverse proxies sit in front of the application servers too.

### What happens if I type a URL without https://?

Many modern browsers try HTTPS first for a typed address. If the site is on the browser's HSTS list, from the preload list or a header seen on an earlier visit, the browser always upgrades to HTTPS before sending anything. Otherwise an HTTP request may be answered with a 301 redirect to the HTTPS address.

### What is the role of a CDN when loading a website?

A content delivery network keeps copies of a site's content on servers in many cities. DNS or anycast routing sends each visitor to a nearby edge server, so the TCP and TLS handshakes and the download cover a short distance, and the origin server is spared most of the traffic.


---

