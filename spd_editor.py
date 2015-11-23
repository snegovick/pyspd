from spd import *
import sys

usage = ""
if len(sys.argv) < 3:
    print usage
    exit(1)

iname = sys.argv[1]
f = open(iname, "r")
bdata = f.read()
f.close()

spd = SPD(bdata)
print spd.info
spd.info['ranks'] = ddr3_ranks_rev[2]
spd.info['sdramwidth'] = ddr3_dev_width_rev[8]
spd.info['sdramcap'] = ddr3_module_capacity_rev[4096]
spd.info['buswidth'] = ddr3_bus_width_rev[16]

oname = sys.argv[2]
f = open(oname, "w")
f.write(spd.encode_ddr3())
f.close()
