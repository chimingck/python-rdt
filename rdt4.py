#!/usr/bin/python3
"""Implementation of RDT4.0
"""

import socket
import random
import struct
import select
import sys
from threading import Timer
import math

#some constants
PAYLOAD = 1000		#size of data payload of each packet
CPORT = 100			#Client port number - Change to your port number
SPORT = 200			#Server port number - Change to your port number
TIMEOUT = 0.05		#retransmission timeout duration
TWAIT = 10*TIMEOUT 	#TimeWait duration

#store peer address info
__peeraddr = ()		#set by rdt_peer()
#define the error rates and window size
__LOSS_RATE = 0.0	#set by rdt_network_init()
__ERR_RATE = 0.0
__W = 1

# self-defined vars
# define the seq no.
__seq_send = 0
__seq_rcev = 0

# reset timeout
__reset_twait = ()

# internal functions - being called within the module
# written by the CS dept
# remains unchanged
def __udt_send(sockd, peer_addr, byte_msg):
	"""This function is for simulating packet loss or corruption in an unreliable channel.

	Input arguments: Unix socket object, peer address 2-tuple and the message
	Return  -> size of data sent, -1 on error
	Note: it does not catch any exception
	"""
	global __LOSS_RATE, __ERR_RATE
	if peer_addr == ():
		print("Socket send error: Peer address not set yet")
		return -1
	else:
		#Simulate packet loss
		drop = random.random()
		if drop < __LOSS_RATE:
			#simulate packet loss of unreliable send
			print("WARNING: udt_send: Packet lost in unreliable layer!!")
			return len(byte_msg)

		#Simulate packet corruption
		corrupt = random.random()
		if corrupt < __ERR_RATE:
			err_bytearr = bytearray(byte_msg)
			pos = random.randint(0,len(byte_msg)-1)
			val = err_bytearr[pos]
			if val > 1:
				err_bytearr[pos] -= 2
			else:
				err_bytearr[pos] = 254
			err_msg = bytes(err_bytearr)
			print("WARNING: udt_send: Packet corrupted in unreliable layer!!")
			return sockd.sendto(err_msg, peer_addr)
		else:
			return sockd.sendto(byte_msg, peer_addr)

# written by the CS dept
# remains unchanged
def __udt_recv(sockd, length):
	"""Retrieve message from underlying layer

	Input arguments: Unix socket object and the max amount of data to be received
	Return  -> the received bytes message object
	Note: it does not catch any exception
	"""
	(rmsg, peer) = sockd.recvfrom(length)
	return rmsg

# written by the CS dept
# remains unchanged
def __IntChksum(byte_msg):
	"""Implement the Internet Checksum algorithm

	Input argument: the bytes message object
	Return  -> 16-bit checksum value
	Note: it does not check whether the input object is a bytes object
	"""
	total = 0
	length = len(byte_msg)	#length of the byte message object
	i = 0
	while length > 1:
		total += ((byte_msg[i+1] << 8) & 0xFF00) + ((byte_msg[i]) & 0xFF)
		i += 2
		length -= 2

	if length > 0:
		total += (byte_msg[i] & 0xFF)

	while (total >> 16) > 0:
		total = (total & 0xFFFF) + (total >> 16)

	total = ~total

	return total & 0xFFFF


#These are the functions used by appliation

# written by the CS dept
# remains unchanged
def rdt_network_init(drop_rate, err_rate, W):
	"""Application calls this function to set properties of underlying network.

    Input arguments: packet drop probability, packet corruption probability and Window size
	"""
	random.seed()
	global __LOSS_RATE, __ERR_RATE, __W
	__LOSS_RATE = float(drop_rate)
	__ERR_RATE = float(err_rate)
	__W = int(W)
	print("Drop rate:", __LOSS_RATE, "\tError rate:", __ERR_RATE, "\tWindow size:", __W)

# written by the CS dept
# remains unchanged
def rdt_socket():
	"""Application calls this function to create the RDT socket.

	Null input.
	Return the Unix socket object on success, None on error

	Note: Catch any known error and report to the user.
	"""
	# same as rdt1, use the standard UDP socket
	try:
		sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error as emsg:
		print("Socket creation error: ", emsg)
		return None
	return sd

# written by the CS dept
# remains unchanged
def rdt_bind(sockd, port):
	"""Application calls this function to specify the port number
	used by itself and assigns them to the RDT socket.

	Input arguments: RDT socket object and port number
	Return	-> 0 on success, -1 on error

	Note: Catch any known error and report to the user.
	"""
	# same as rdt1, use the standard way
	try:
		sockd.bind(("",port))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		return -1
	return 0

# written by the CS dept
# remains unchanged
def rdt_peer(peer_ip, port):
	"""Application calls this function to specify the IP address
	and port number used by remote peer process.

	Input arguments: peer's IP address and port number
	"""
	# same as rdt1, use the standard way
	global __peeraddr
	__peeraddr = (peer_ip, port)



# ===============================================================
# Code below's written by me
def rdt_send(sockd, byte_msg):
	"""Application calls this function to transmit a message (up to
	W * PAYLOAD bytes) to the remote peer through the RDT socket.

	Input arguments: RDT socket object and the message bytes object
	Return  -> size of data sent on success, -1 on error

	Note: (1) This function will return only when it knows that the
	whole message has been successfully delivered to remote process.
	(2) Catch any known error and report to the user.
	"""
	global PAYLOAD,TIMEOUT, __W, __peeraddr, __seq_send

	# double check max payload size
	if (len(byte_msg) > PAYLOAD * __W):
		msg = byte_msg[0:PAYLOAD * __W]
	else:
		msg = byte_msg

	# count # of packet N
	N = math.ceil( len(msg) / PAYLOAD )
	# print("len(msg): %d, PAYLOAD: %d, N: %d" % (len(msg), PAYLOAD, N))

	send_packets = []
	# only need to store the last acked #
	send_packets_ack = -1
	start_seq = __seq_send

	# send out N packages
	for i in range (1, N+1):
		if (i < N):
			msg_to_send = msg[PAYLOAD*(i-1):PAYLOAD*i]
			payload_length = PAYLOAD
		else: # i == N
			msg_to_send = msg[PAYLOAD*(N-1):]
			payload_length = len(msg_to_send)

		# in Bytes [type, seq, pad, pad, payload len, payload len]
		# Big Endian
		format_str = '!2B2x1H' + str(payload_length) + 's'
		packet = struct.pack(format_str, 12, __seq_send, payload_length, msg_to_send)

		checksum = __IntChksum(packet)
		packet = packet[0:2] + struct.pack('=1H', checksum) + packet[4:]
		# packet = packet[0:2] + checksum.to_bytes(2, 'big') + packet[4:]
		# print('sending packet:')
		# print('checksum: ',checksum, checksum.to_bytes(2, 'big'))
		# print('msg length: ',payload_length, payload_length.to_bytes(2, 'big'))
		# print(packet)
		send_packets.append(packet)

		try:
			pckLength = __udt_send(sockd, __peeraddr, packet)
		except socket.error as emsg:
			print("Socket send error: ", emsg)
			return -1

		# max. seq = 2^8 - 1
		# depends on the no. of bits of seq. no.
		__seq_send = (__seq_send + 1) % 256

	while True:
		try:
			Rready, Wready, Eready = select.select([sockd], [], [], TIMEOUT)
		except select.error as emsg:
			print("At select, caught an exception:", emsg)
			return -1
		except KeyboardInterrupt:
			print("At select, caught the KeyboardInterrupt")
			return -1

		# if has incoming activities
		if Rready:
			try:
				rmsg = __udt_recv(sockd, PAYLOAD + 6)
				if rmsg:
					# checksum, apply
					recv_header = struct.unpack("!2B", rmsg[:2]) + struct.unpack("=1H", rmsg[2:4]) + struct.unpack("!1H", rmsg[4:6])
					# print(recv_header)
					recv_type = 'DATA' if recv_header[0] == 12 else 'ACK'
					# checksum
					rmsg_no_checksum = rmsg[0:2] + [0][0].to_bytes(2, 'big') + rmsg[4:]
					# print(recv_header[2])
					if (__IntChksum(rmsg_no_checksum) != recv_header[2]):
						print('Received a corrupted packet: Type = %s, Length = %d' % (recv_type, len(rmsg)))
						print('Drop the packet')
						continue
					
					# If need to access the payload data
					# if (recv_header[3] > 0):
					# 	rcev_payload = struct.unpack("!%ds" % recv_header[3], rmsg[6:])

					# if it's ACK
					if (recv_header[0] == 11):

						recv_ack = recv_header[1]

						if (recv_ack == __seq_send - 1 or (recv_ack == 255 and __seq_send == 0)):
							# received the last ACK
							# sent successfully
							print("Received the ACK with seqNo.: %d" % recv_ack)
							print("rdt_send: Sent one message of size %d" % len(msg))
							return len(msg)

						elif (__is_ack_between(recv_ack, start_seq, __seq_send - 2)):
							# received a valid ACK
							print("Received the ACK with seqNo.: %d" % recv_ack)
							send_packets_ack = recv_ack
							continue

						# if (!__is_ack_between(recv_header[1], start_seq, start_seq + N - 1)):
						else: # ack is NOT between start_seq, start_seq+N-1, invalid
							print("Received an out-of-window ACK with seqNo.: %d" % recv_ack)
							continue

					# else if it's DATA
					else:
						print('I am expecting an ACK packet, but received a DATA packet')
						recv_seq = recv_header[1]

						if (recv_seq == __seq_rcev):
							print('peer sent me a new DATA packet!!')
							print('Drop the packet as I cannot accept it at this point')
						else:
							print('Received a retransmission DATA packet from peer!!')
							print('retransmit the ACK packet!!')

							# resend the last in-order ACK
							seq = __seq_rcev - 1
							if (seq < 0):
								seq = 255 # max. no. of ack which is 2^k, k is the no. of bits for storing seq.no.

							__send_ack(sockd, __peeraddr, seq)
							continue

			except socket.error as emsg:
				print("Socket recv error: ", emsg)
				return -1

		# TIMEOUT,
		# retransmit all DATA packet which not yet been acknowledged
		else:
			if (send_packets_ack == -1):
				resend_from = start_seq
			else:
				resend_from = (send_packets_ack + 1) % 256

			resend_to = __seq_send - 1
			if (resend_to == -1):
				resend_to = 255

			print("Timeout!! Retransmit the packet from seqNo. %d to seqNo. %d again" % (resend_from, resend_to))
			for i in range(1, N + 1):
				seq = (start_seq + i - 1) % 256 # 2^k, k is no. of bits for storing seq.no.
				if __is_ack_between(seq, resend_from, resend_to):
					print("Retransmitting packet with seqNo.: %d" % seq)
					try:
						pckLength = __udt_send(sockd, __peeraddr, send_packets[i-1])
					except socket.error as emsg:
						print("Socket send error: ", emsg)
						return -1

def rdt_recv(sockd, length):
	"""Application calls this function to wait for a message from the
	remote peer; the caller will be blocked waiting for the arrival of
	the message. Upon receiving a message from the underlying UDT layer,
    the function returns immediately.

	Input arguments: RDT socket object and the size of the message to
	received.
	Return  -> the received bytes message object on success, b'' on error

	Note: Catch any known error and report to the user.
	"""
	global __seq_rcev, __reset_twait

	while True:
		try:
			# print('receiving packet:')
			rmsg = __udt_recv(sockd, length + 6)
			if rmsg:
				# print(rmsg) 
				recv_header = struct.unpack("!2B", rmsg[:2]) + struct.unpack("=1H", rmsg[2:4]) + struct.unpack("!1H", rmsg[4:6])
				recv_type = 'DATA' if recv_header[0] == 12 else 'ACK'
				# checksum
				rmsg_no_checksum = rmsg[0:2] + [0][0].to_bytes(2, 'big') + rmsg[4:]
				# print(recv_header[2])
				if (__IntChksum(rmsg_no_checksum) != recv_header[2]):
					print('Received a corrupted packet: Type = %s, Length = %d' % (recv_type, len(rmsg)))
					print('Drop the packet')
					continue

				# if it is a DATA packet
				if (recv_type == 'DATA'):

					if (__reset_twait == False):
						__reset_twait = True

					if (recv_header[1] == __seq_rcev):
						print('Got an expected packet with seqNo.: %d' % __seq_rcev)

						__send_ack(sockd, __peeraddr, __seq_rcev)

						print('Received a message of size :%d' % len(rmsg))

						__seq_rcev = (__seq_rcev + 1) % 256

						if (recv_header[3] > 0):
							rcev_payload = struct.unpack("!%ds" % recv_header[3], rmsg[6:])
							# print(rcev_payload)
							return rcev_payload[0]
						else:
							return b''

					else:
						print('Received a retransmission or out-of-order DATA packet from peer!!')
						seq = __seq_rcev - 1
						if (seq < 0):
							seq = 255 # max. no. of ack which is 2^k, k is the no. of bits for storing seq.no.

						__send_ack(sockd, __peeraddr, seq)
						continue
				
				# (recv_type == 'ACK')
				else:
					print('Received unexpected ACK!')	
					print('Drop the packet')

		except socket.error as emsg:
			if (__reset_twait == ()):
				print("Socket recv error: ", emsg)
			return b''

def rdt_close(sockd):
	"""Application calls this function to close the RDT socket.

	Input argument: RDT socket object

	Note: (1) Catch any known error and report to the user.
	(2) Before closing the RDT socket, the reliable layer needs to wait for TWAIT
	time units before closing the socket.
	"""
	global TWAIT, PAYLOAD, __reset_twait

	# avoid repeated call by checking == ()
	if __reset_twait == ():
		__reset_twait = False
		# multithread unblocking timeout function
		t = Timer(TWAIT, __close, [sockd])
		t.start()

		rdt_recv(sockd, PAYLOAD + 6)

# My internal functions

def __close(sockd):
	global __reset_twait, TWAIT

	# duplicated calls of sdt_close()
	if __reset_twait == ():
		return

	if __reset_twait:
		__reset_twait = False
		t = Timer(TWAIT, __close, [sockd])
		t.start()

	else:
		try:
			sockd.close()
		except socket.error as emsg:
			print("Socket close error: ", emsg)

# send an ack with given seq. no.
def __send_ack(sockd, peeraddr, seq):
	ack_packet = struct.pack('!2B2x1H', 11, seq, 0)

	checksum = __IntChksum(ack_packet)
	ack_packet = ack_packet[0:2] + struct.pack('=1H', checksum) + ack_packet[4:]
	
	try:
		pckLength = __udt_send(sockd, peeraddr, ack_packet)
	except socket.error as emsg:
		print("Socket send error: ", emsg)
	return -1

# check whether a given seq is in between two seq. no. or not, inclusive
# handled wrapped around seq. no
# e.g. (start_seq 250 < ack_seq 255 < end_seq 3) will return True
def __is_ack_between(ack_seq, start_seq, end_seq):
	# assume windows size W < 2^k, k is the # of bits for storing seq #
	# if seq # wrapped around
	if (end_seq < start_seq):
		end_seq += 256 # 2^k
		if (ack_seq <= start_seq + __W - 256):
			ack_seq += 256

	return (start_seq <= ack_seq <= end_seq)