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
import tarfile

class builder():
	def __init__(self, inPath, outRoot):
		self.inPath = inPath
		self.outRoot = outRoot
		self.dirPathGenBak = "../gen_bak"
		self.toolCreateNvs = "tools/nvs_partition_gen.py"

	def procLine(self, line):
		line = line.strip()
		cols = line.split(",")
		if len(cols) < 3:
			print(f"Bad line {line}")
			return False

		serNum  = cols[0].strip()
		macBase = cols[1].strip()
		popCode = cols[2].strip()

		mfgPath = os.path.join(self.outRoot, "units", f"{serNum}")

		if os.path.exists(mfgPath):
			# Start with a clean directory
			fileList = os.listdir(mfgPath) 
			for f in fileList:
				os.remove(os.path.join(mfgPath, f))
		else:
			# Create the directory
			os.makedirs(mfgPath)

		csvPath = os.path.join(mfgPath, "mfg_data.csv")

		with open(csvPath, "wt") as fh:
			# Put the two required header lines
			fh.write("key,type,encoding,value\n")
			fh.write("mfg,namespace,,\n")
			fh.write(f"serial_num,data,string,{serNum}\n")
			fh.write(f"mac_addr_base,data,hex2bin,{macBase}\n")
			fh.write(f"pop_code,data,string,{popCode}\n")

		binPath = os.path.join(mfgPath, "mfg_data.bin")

		if os.path.exists(binPath):
			os.remove(binPath)

		cmd = ["python3", self.toolCreateNvs, "generate", csvPath, binPath, "0x4000"]
		try:
			subprocess.check_output(cmd)
		except OSError:
			print(f"Tool not found: {self.toolCreateNvs}")
			return False
		except subprocess.CalledProcessError:
			print("MFG data generation failed")
			return False

		if not os.path.exists(self.dirPathGenBak):
			os.makedirs(self.dirPathGenBak)

		for i in range(1, 100):
			fname = f"gen-{serNum}-{i:02}.tar.gz"
			genBakTar = os.path.join(self.dirPathGenBak, fname)
			if not os.path.exists(genBakTar):
				tf = tarfile.open(name=genBakTar, mode="w:gz")
				tf.add(mfgPath)
				tf.close()
				break

		return True

def main() -> int:
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'input',
		help=f'CSV file with production data'
	)
	parser.add_argument(
		'output',
		help=f'Root folder to place generated files'
	)

	arg = parser.parse_args()

	try:
		bld = builder(arg.input, arg.output)
	except Exception as e:
		print(f'Failed to initialize builder: {e}')
		return 1

	if not os.path.exists(arg.input):
		print("Input file not found")

	with open(arg.input, "rt") as inp:
		lineCt = 0
		buildCt = 0
		for line in inp:
			lineCt += 1
			if 1 == lineCt:
				# Skip header line
				continue
			else:
				success = bld.procLine(line)
				if success:
					buildCt += 1
				else:
					break

	print(f"{buildCt} files created")
	return 0

if __name__ == "__main__":
	ret = main()
	sys.exit(ret)
