import sys

usage = ""

if len(sys.argv) < 3:
    print usage
    exit(1)
    
inname = sys.argv[1]
oname = sys.argv[2]

f = open(inname, "r")
data = f.read()
f.close()

bdata = "".join(map(lambda b: chr(int(b, 16)), data.split(",")))

ofile = open(oname, "w")
ofile.write(bdata)
ofile.close()
