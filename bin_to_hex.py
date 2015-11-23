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

out = ""
for i, b in enumerate(data):
    out+=hex(ord(b))+", "
    if (i+1) % 8 == 0:
        out+="\\\n"

ofile = open(oname, "w")
ofile.write(out)
ofile.close()
