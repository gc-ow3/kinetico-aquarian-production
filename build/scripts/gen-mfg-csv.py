#!/usr/bin/env python3
#
#
import os
import os.path
import sys
import platform
import subprocess
import datetime
import re
import random
import argparse
import time
import json

class macAddr():
	def __init__(self, filePath, step):
		if step not in [1, 2, 4]:
			raise ValueError('Invalid step value')

		self.macFile = filePath
		self.macStep = step

		try:
			with open(self.macFile, 'r') as fh:
				inFile = (fh.read()).split('\n')
		except:
			raise

		macData = ''
		for line in inFile:
			if len(line) == 0 or line[0] == '#':
				# Skip empty lines and comment lines
				continue
			else:
				macData = line.split(',')
				break

		# Expected 3 comma-seperated values
		if len(macData) != 3:
			raise RuntimeError('Badly formatted MAC address file')

		# Validate the data is proper format
		for i in range(0, 3):
			if re.match(r"[0-9a-fA-F]{12}$", macData[i]) == None:
				raise RuntimeError(f'Not proper MAC format: {macData[i]}')

		self.macStart = int(macData[0], 16)
		self.macEnd   = int(macData[1], 16)
		self.macCurr  = int(macData[2], 16)

		# Verify MAC address aligns with step
		if self.macCurr % self.macStep != 0:
			raise RuntimeError(f'Misaligned starting MAC address ({self.macCurr:012x})')

		if self.macCurr + self.macStep > self.macEnd:
			# Available list of addresses used up
			raise RuntimeError('Not enough MAC addresses available')

		self.macAvailable = (self.macEnd - self.macCurr + self.macStep) / self.macStep
		#print(f'Available # of MAC addresses: {self.macAvailable}')

	def __save__(self) -> bool:
		macData = [
			f'{self.macStart:012x}',
			f'{self.macEnd:012x}',
			f'{self.macCurr:012x}'
		]

		macLine = ','.join(macData)

		with open(self.macFile, 'r') as fh:
			inFile = fh.read()

		outFile = ''
		for line in inFile:
			if len(line) == 0 or line[0] == '#':
				# Copy empty lines and comment lines
				outFile += line + '\n'
			else:
				# Write the new MAC address line
				outFile += macLine + '\n'
				break

		with open(self.macFile, 'w') as fh:
			fh.write(outFile)

		return True

	def available(self) -> int:
		return self.macAvailable

	def get(self) -> str:
		if self.macCurr > self.macEnd:
			# Available list of addresses used up
			print('No MAC address available')
			return None

		# Set the MAC address to be returned
		retVal = f'{self.macCurr:012x}'

		# Increment the next MAC address
		self.macCurr += self.macStep

		# Update the file for each allocation
		if self.__save__():
			return retVal
		else:
			return None


def genPopCode() -> str:
	return f"{random.randint(0, 9999):04}"


class builder():
	def __init__(self, macFile):
		'''Set up MAC address manager to allocate 4 sequential MAC addresses for each unit: Wi-Fi AP, Wi-Fi STA, BLE, Ethernet'''
		try:
			self.macAddr = macAddr(macFile, 4)
		except:
			raise


def main() -> int:
	dfltMAC = os.path.join('prod_db', 'mac_addr.txt')
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'--mac_file',
		type=str,
		default=dfltMAC,
		help=f'path to MAC address file (default: {dfltMAC}'
	)
	parser.add_argument(
		'--count', '-c',
		type=int,
		required=True,
		help='Number of data sets to generate'
	)
	parser.add_argument(
		'output',
		help=f'Output file'
	)

	arg = parser.parse_args()

	try:
		bld = builder(arg.mac_file)
	except Exception as e:
		print(f'Failed to initialize builder: {e}')
		return 1

	with open(arg.output, "wt") as fh:
		fh.write("serial_num,mac_base_addr,pop_code,qr_code\n")

	genCount = 0
	for _ in range(arg.count):
		# Get base MAC address
		macBase = bld.macAddr.get()
		if macBase is None:
			return 1

		# BLE MAC is base MAC plus 2
		macBLE = f"{int(macBase, 16) + 2:012x}"
		popCode = genPopCode()

		# Build the QR label data
		qrCode = f'"{macBase},{macBLE},{popCode}"'

		# For this product base MAC address and serial number are the same
		with open(arg.output, "at") as fh:
			fh.write(f"{macBase},{macBase},{popCode},{qrCode}\n")
		genCount += 1

	# Successful completion
	print(f"{genCount} records created")
	return 0

if __name__ == "__main__":
	ret = main()
	sys.exit(ret)
