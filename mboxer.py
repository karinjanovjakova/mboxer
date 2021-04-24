#!/usr/bin/env python3
import socket
import os
import sys
import signal
import hashlib


def kontrola_riadku_hlavicky(h):
	nazov = ""
	popis = ""
	if not h.isascii():
		return (nazov, popis)
	if h.find(":") != -1:			#ak našiel oddeľovaciu : a je práve jedna
		zoz=h.split(":")
		if len(zoz)!=2:			
			return (nazov, popis)
		if h.find("/") == -1 and h.find(" ") == -1:	#ak nenašiel / alebo medzeru  >> vsetko ok
			nazov=zoz[0]
			popis=zoz[1]
		else:
			return (nazov, popis)
	else:
		return (nazov, popis)
	return (nazov, popis)

def kontrola_hlaviciek(headers):
	status_number = 100
	status_text = "OK"
	for i in headers:
		if i=="" or headers[i]=="" :
			status_number, status_text = (200, "Bad request")
			return (status_number, status_text)
	return (status_number, status_text)

def metoda_write(headers, f):
	status_number=100
	status_text="OK"
	content=""
	content_header=""
	try:
		content_text = f.read(int(headers["Content-length"]))
		name = hashlib.md5(content_text.encode("utf-8")).hexdigest()

		with open(f'{headers["Mailbox"]}/{name}',"w") as file:
			file.write(content_text)
	except KeyError:
		status_number,status_text=(200,"Bad request")
	except ValueError:
		status_number,status_text=(200,"Bad request")
	except FileNotFoundError:
		status_number,status_text=(203,"No such mailbox")
	return (status_number, status_text, content_header, content)

def metoda_read(headers): 
	status_number=100
	status_text="OK"
	content=""
	content_header=""
	try:
		with open(f'{headers["Mailbox"]}/{headers["Message"]}', "r") as file:
			content=file.read()
			content_header=(f'Content-length:{len(content)}\n')
	except KeyError: 
		status_number, status_text = (200, "Bad request")
	except FileNotFoundError: 
		status_number, status_text = (201, "No such message")
	except OSError: 
		status_number, status_text = (202, "Read error")
	return (status_number, status_text, content_header, content)


def metoda_ls(headers):
	status_number=100
	status_text="OK"
	content=""
	content_header=""
	try:
		dire = os.listdir(headers["Mailbox"])
		content_header = (f'Number-of-messages:{len(dire)}')
		content = "\n".join(dire)+ "\n"
	except KeyError: 
		status_number, status_text = (200, "Bad request")
	except FileNotFoundError:
		status_number, status_text = (203, "No such mailbox")
	return (status_number, status_text, content_header, content)



s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('',9999))
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
s.listen(5)

while True:
	connected_socket,address=s.accept()
	print(f'spojenie z {address}')
	pid_chld=os.fork()
	if pid_chld==0:
		s.close()
		f=connected_socket.makefile("rw")
		while True:
			resp_header = ""
			response = ""
			headers = {}
			metoda=f.readline()
			metoda=metoda.strip()
			h=f.readline()
			while h!="\n":
				h=h.strip()
				nazov, popis=kontrola_riadku_hlavicky(h)
				headers[nazov]=popis
				h=f.readline()
			headers_status, headers_status_text = kontrola_hlaviciek(headers)
			if headers_status==100:		                                
				if metoda == "WRITE":
					status_number, status_text,resp_header,response=metoda_write(headers, f)
				elif metoda == "READ":
					status_number, status_text,resp_header,response=metoda_read(headers)
				elif metoda == "LS":
					(status_number, status_text,resp_header,response)=metoda_ls(headers)
				else:
					status_number, status_text=(204,"Unknown method")
					f.write(f'{status_number} {status_text}')
					f.write('\n\n')
					f.flush()
					sys.exit(0)
			else:
				status_number, status_text=(200,"Bad request")
				f.write(f'{status_number} {status_text}')
				f.write('\n\n')
				f.flush()
				sys.exit(0)
			f.write(f'{status_number} {status_text}')
			f.write('\n')
			f.write(resp_header)
			f.write('\n')
			f.write(response)
			f.flush()
			print(f'{address} uzavrel spojenie')
		sys.exit(0)
	else:
		connected_socket.close()


