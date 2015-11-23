from spd import SPD
import sys

usage = ""
if len(sys.argv) < 2:
    print usage
    exit(1)

iname = sys.argv[1]
f = open(iname, "r")
bdata = f.read()
f.close()

spd = SPD(bdata)
print spd.info
