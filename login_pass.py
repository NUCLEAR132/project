def enc(Code,num=26,C=1):
		if C == 1:
			code = ""
			for i in Code:
				i = int(ord(i)) / int(num)
				b = str(i)
				code += b
				code = code[0:100]
		return code