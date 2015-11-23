# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding=utf8

# Copyright 2015 Lenovo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This implements parsing of DDR SPD data.  This is offered up in a pass
# through fashion by some service processors.

# For now, just doing DDR3 and DDR4

# In many cases, astute readers will note that some of the lookup tables
# should be a matter of math rather than lookup.  However the SPD
# specification explicitly reserves values not in the lookup tables for
# future use.  It has happened, for example, that a spec was amended
# with discontinuous values for a field that was until that point
# possible to derive in a formulaic way

import struct
import math

jedec_ids = [
    {
        0x01: "AMD",
        0x02: "AMI",
        0x83: "Fairchild",
        0x04: "Fujitsu",
        0x85: "GTE",
        0x86: "Harris",
        0x07: "Hitachi",
        0x08: "Inmos",
        0x89: "Intel",
        0x8a: "I.T.T.",
        0x0b: "Intersil",
        0x8c: "Monolithic Memories",
        0x0d: "Mostek",
        0x0e: "Motorola",
        0x8f: "National",
        0x10: "NEC",
        0x91: "RCA",
        0x92: "Raytheon",
        0x13: "Conexant (Rockwell)",
        0x94: "Seeq",
        0x15: "Philips Semi. (Signetics)",
        0x16: "Synertek",
        0x97: "Texas Instruments",
        0x98: "Toshiba",
        0x19: "Xicor",
        0x1a: "Zilog",
        0x9b: "Eurotechnique",
        0x1c: "Mitsubishi",
        0x9d: "Lucent (AT&T)",
        0x9e: "Exel",
        0x1f: "Atmel",
        0x20: "SGS/Thomson",
        0xa1: "Lattice Semi.",
        0xa2: "NCR",
        0x23: "Wafer Scale Integration",
        0xa4: "IBM",
        0x25: "Tristar",
        0x26: "Visic",
        0xa7: "Intl. CMOS Technology",
        0xa8: "SSSI",
        0x29: "Microchip Technology",
        0x2a: "Ricoh Ltd.",
        0xab: "VLSI",
        0x2c: "Micron Technology",
        0xad: "Hyundai Electronics",
        0xae: "OKI Semiconductor",
        0x2f: "ACTEL",
        0xb0: "Sharp",
        0x31: "Catalyst",
        0x32: "Panasonic",
        0xb3: "IDT",
        0x34: "Cypress",
        0xb5: "DEC",
        0xb6: "LSI Logic",
        0x37: "Zarlink",
        0x38: "UTMC",
        0xb9: "Thinking Machine",
        0xba: "Thomson CSF",
        0x3b: "Integrated CMOS(Vertex)",
        0xbc: "Honeywell",
        0x3d: "Tektronix",
        0x3e: "Sun Microsystems",
        0xbf: "SST",
        0x40: "MOSEL",
        0xc1: "Infineon",
        0xc2: "Macronix",
        0x43: "Xerox",
        0xc4: "Plus Logic",
        0x45: "SunDisk",
        0x46: "Elan Circuit Tech.",
        0xc7: "European Silicon Str.",
        0xc8: "Apple Computer",
        0xc9: "Xilinx",
        0x4a: "Compaq",
        0xcb: "Protocol Engines",
        0x4c: "SCI",
        0xcd: "Seiko Instruments",
        0xce: "Samsung",
        0x4f: "I3 Design System",
        0xd0: "Klic",
        0x51: "Crosspoint Solutions",
        0x52: "Alliance Semiconductor",
        0xd3: "Tandem",
        0x54: "Hewlett-Packard",
        0xd5: "Intg. Silicon Solutions",
        0xd6: "Brooktree",
        0x57: "New Media",
        0x58: "MHS Electronic",
        0xd9: "Performance Semi.",
        0xda: "Winbond Electronic",
        0x5b: "Kawasaki Steel",
        0xdc: "Bright Micro",
        0x5d: "TECMAR",
        0x5e: "Exar",
        0xdf: "PCMCIA",
        0xe0: "LG Semiconductor",
        0x61: "Northern Telecom",
        0x62: "Sanyo",
        0xe3: "Array Microsystems",
        0x64: "Crystal Semiconductor",
        0xe5: "Analog Devices",
        0xe6: "PMC-Sierra",
        0x67: "Asparix",
        0x68: "Convex Computer",
        0xe9: "Quality Semiconductor",
        0xea: "Nimbus Technology",
        0x6b: "Transwitch",
        0xec: "Micronas (ITT Intermetall)",
        0x6d: "Cannon",
        0x6e: "Altera",
        0xef: "NEXCOM",
        0x70: "QUALCOMM",
        0xf1: "Sony",
        0xf2: "Cray Research",
        0x73: "AMS (Austria Micro)",
        0xf4: "Vitesse",
        0x75: "Aster Electronics",
        0x76: "Bay Networks (Synoptic)",
        0xf7: "Zentrum",
        0xf8: "TRW",
        0x79: "Thesys",
        0x7a: "Solbourne Computer",
        0xfb: "Allied-Signal",
        0x7c: "Dialog",
        0xfd: "Media Vision",
        0xfe: "Level One Communication",
    },
    {
        0x01: "Cirrus Logic",
        0x02: "National Instruments",
        0x83: "ILC Data Device",
        0x04: "Alcatel Mietec",
        0x85: "Micro Linear",
        0x86: "Univ. of NC",
        0x07: "JTAG Technologies",
        0x08: "Loral",
        0x89: "Nchip",
        0x8A: "Galileo Tech",
        0x0B: "Bestlink Systems",
        0x8C: "Graychip",
        0x0D: "GENNUM",
        0x0E: "VideoLogic",
        0x8F: "Robert Bosch",
        0x10: "Chip Express",
        0x91: "DATARAM",
        0x92: "United Microelec Corp.",
        0x13: "TCSI",
        0x94: "Smart Modular",
        0x15: "Hughes Aircraft",
        0x16: "Lanstar Semiconductor",
        0x97: "Qlogic",
        0x98: "Kingston",
        0x19: "Music Semi",
        0x1A: "Ericsson Components",
        0x9B: "SpaSE",
        0x1C: "Eon Silicon Devices",
        0x9D: "Programmable Micro Corp",
        0x9E: "DoD",
        0x1F: "Integ. Memories Tech.",
        0x20: "Corollary Inc.",
        0xA1: "Dallas Semiconductor",
        0xA2: "Omnivision",
        0x23: "EIV(Switzerland)",
        0xA4: "Novatel Wireless",
        0x25: "Zarlink (formerly Mitel)",
        0x26: "Clearpoint",
        0xA7: "Cabletron",
        0xA8: "Silicon Technology",
        0x29: "Vanguard",
        0x2A: "Hagiwara Sys-Com",
        0xAB: "Vantis",
        0x2C: "Celestica",
        0xAD: "Century",
        0xAE: "Hal Computers",
        0x2F: "Rohm Company Ltd.",
        0xB0: "Juniper Networks",
        0x31: "Libit Signal Processing",
        0x32: "Enhanced Memories Inc.",
        0xB3: "Tundra Semiconductor",
        0x34: "Adaptec Inc.",
        0xB5: "LightSpeed Semi.",
        0xB6: "ZSP Corp.",
        0x37: "AMIC Technology",
        0x38: "Adobe Systems",
        0xB9: "Dynachip",
        0xBA: "PNY Electronics",
        0x3B: "Newport Digital",
        0xBC: "MMC Networks",
        0x3D: "T Square",
        0x3E: "Seiko Epson",
        0xBF: "Broadcom",
        0x40: "Viking Components",
        0xC1: "V3 Semiconductor",
        0xC2: "Flextronics (formerly Orbit)",
        0x43: "Suwa Electronics",
        0xC4: "Transmeta",
        0x45: "Micron CMS",
        0x46: "American Computer & Digital Components Inc",
        0xC7: "Enhance 3000 Inc",
        0xC8: "Tower Semiconductor",
        0x49: "CPU Design",
        0x4A: "Price Point",
        0xCB: "Maxim Integrated Product",
        0x4C: "Tellabs",
        0xCD: "Centaur Technology",
        0xCE: "Unigen Corporation",
        0x4F: "Transcend Information",
        0xD0: "Memory Card Technology",
        0x51: "CKD Corporation Ltd.",
        0x52: "Capital Instruments, Inc.",
        0xD3: "Aica Kogyo, Ltd.",
        0x54: "Linvex Technology",
        0xD5: "MSC Vertriebs GmbH",
        0xD6: "AKM Company, Ltd.",
        0x57: "Dynamem, Inc.",
        0x58: "NERA ASA",
        0xD9: "GSI Technology",
        0xDA: "Dane-Elec (C Memory)",
        0x5B: "Acorn Computers",
        0xDC: "Lara Technology",
        0x5D: "Oak Technology, Inc.",
        0x5E: "Itec Memory",
        0xDF: "Tanisys Technology",
        0xE0: "Truevision",
        0x61: "Wintec Industries",
        0x62: "Super PC Memory",
        0xE3: "MGV Memory",
        0x64: "Galvantech",
        0xE5: "Gadzoox Nteworks",
        0xE6: "Multi Dimensional Cons.",
        0x67: "GateField",
        0x68: "Integrated Memory System",
        0xE9: "Triscend",
        0xEA: "XaQti",
        0x6B: "Goldenram",
        0xEC: "Clear Logic",
        0x6D: "Cimaron Communications",
        0x6E: "Nippon Steel Semi. Corp.",
        0xEF: "Advantage Memory",
        0x70: "AMCC",
        0xF1: "LeCroy",
        0xF2: "Yamaha Corporation",
        0x73: "Digital Microwave",
        0xF4: "NetLogic Microsystems",
        0x75: "MIMOS Semiconductor",
        0x76: "Advanced Fibre",
        0xF7: "BF Goodrich Data.",
        0xF8: "Epigram",
        0x79: "Acbel Polytech Inc.",
        0x7A: "Apacer Technology",
        0xFB: "Admor Memory",
        0x7C: "FOXCONN",
        0xFD: "Quadratics Superconductor",
        0xFE: "3COM",
    },
    {
        0x01: "Camintonn Corporation",
        0x02: "ISOA Incorporated",
        0x83: "Agate Semiconductor",
        0x04: "ADMtek Incorporated",
        0x85: "HYPERTEC",
        0x86: "Adhoc Technologies",
        0x07: "MOSAID Technologies",
        0x08: "Ardent Technologies",
        0x89: "Switchcore",
        0x8A: "Cisco Systems, Inc.",
        0x0B: "Allayer Technologies",
        0x8C: "WorkX AG",
        0x0D: "Oasis Semiconductor",
        0x0E: "Novanet Semiconductor",
        0x8F: "E-M Solutions",
        0x10: "Power General",
        0x91: "Advanced Hardware Arch.",
        0x92: "Inova Semiconductors GmbH",
        0x13: "Telocity",
        0x94: "Delkin Devices",
        0x15: "Symagery Microsystems",
        0x16: "C-Port Corporation",
        0x97: "SiberCore Technologies",
        0x98: "Southland Microsystems",
        0x19: "Malleable Technologies",
        0x1A: "Kendin Communications",
        0x9B: "Great Technology Microcomputer",
        0x1C: "Sanmina Corporation",
        0x9D: "HADCO Corporation",
        0x9E: "Corsair",
        0x1F: "Actrans System Inc.",
        0x20: "ALPHA Technologies",
        0xA1: "Cygnal Integrated Products Incorporated",
        0xA2: "Artesyn Technologies",
        0x23: "Align Manufacturing",
        0xA4: "Peregrine Semiconductor",
        0x25: "Chameleon Systems",
        0x26: "Aplus Flash Technology",
        0xA7: "MIPS Technologies",
        0xA8: "Chrysalis ITS",
        0x29: "ADTEC Corporation",
        0x2A: "Kentron Technologies",
        0xAB: "Win Technologies",
        0x2C: "ASIC Designs Inc",
        0xAD: "Extreme Packet Devices",
        0xAE: "RF Micro Devices",
        0x2F: "Siemens AG",
        0xB0: "Sarnoff Corporation",
        0x31: "Itautec Philco SA",
        0x32: "Radiata Inc.",
        0xB3: "Benchmark Elect. (AVEX)",
        0x34: "Legend",
        0xB5: "SpecTek Incorporated",
        0xB6: "Hi/fn",
        0x37: "Enikia Incorporated",
        0x38: "SwitchOn Networks",
        0xB9: "AANetcom Incorporated",
        0xBA: "Micro Memory Bank",
        0x3B: "ESS Technology",
        0xBC: "Virata Corporation",
        0x3D: "Excess Bandwidth",
        0x3E: "West Bay Semiconductor",
        0xBF: "DSP Group",
        0x40: "Newport Communications",
        0xC1: "Chip2Chip Incorporated",
        0xC2: "Phobos Corporation",
        0x43: "Intellitech Corporation",
        0xC4: "Nordic VLSI ASA",
        0x45: "Ishoni Networks",
        0x46: "Silicon Spice",
        0xC7: "Alchemy Semiconductor",
        0xC8: "Agilent Technologies",
        0x49: "Centillium Communications",
        0x4A: "W.L. Gore",
        0xCB: "HanBit Electronics",
        0x4C: "GlobeSpan",
        0xCD: "Element 14",
        0xCE: "Pycon",
        0x4F: "Saifun Semiconductors",
        0xD0: "Sibyte, Incorporated",
        0x51: "MetaLink Technologies",
        0x52: "Feiya Technology",
        0xD3: "I & C Technology",
        0x54: "Shikatronics",
        0xD5: "Elektrobit",
        0xD6: "Megic",
        0x57: "Com-Tier",
        0x58: "Malaysia Micro Solutions",
        0xD9: "Hyperchip",
        0xDA: "Gemstone Communications",
        0x5B: "Anadyne Microelectronics",
        0xDC: "3ParData",
        0x5D: "Mellanox Technologies",
        0x5E: "Tenx Technologies",
        0xDF: "Helix AG",
        0xE0: "Domosys",
        0x61: "Skyup Technology",
        0x62: "HiNT Corporation",
        0xE3: "Chiaro",
        0x64: "MCI Computer GMBH",
        0xE5: "Exbit Technology A/S",
        0xE6: "Integrated Technology Express",
        0x67: "AVED Memory",
        0x68: "Legerity",
        0xE9: "Jasmine Networks",
        0xEA: "Caspian Networks",
        0x6B: "nCUBE",
        0xEC: "Silicon Access Networks",
        0x6D: "FDK Corporation",
        0x6E: "High Bandwidth Access",
        0xEF: "MultiLink Technology",
        0x70: "BRECIS",
        0xF1: "World Wide Packets",
        0xF2: "APW",
        0x73: "Chicory Systems",
        0xF4: "Xstream Logic",
        0x75: "Fast-Chip",
        0x76: "Zucotto Wireless",
        0xF7: "Realchip",
        0xF8: "Galaxy Power",
        0x79: "eSilicon",
        0x7A: "Morphics Technology",
        0xFB: "Accelerant Networks",
        0x7C: "Silicon Wave",
        0xFD: "SandCraft",
        0xFE: "Elpida",
    },
    {
        0x01: "Solectron",
        0x02: "Optosys Technologies",
        0x83: "Buffalo (Formerly Melco)",
        0x04: "TriMedia Technologies",
        0x85: "Cyan Technologies",
        0x86: "Global Locate",
        0x07: "Optillion",
        0x08: "Terago Communications",
        0x89: "Ikanos Communications",
        0x8A: "Princeton Technology",
        0x0B: "Nanya Technology",
        0x8C: "Elite Flash Storage",
        0x0D: "Mysticom",
        0x0E: "LightSand Communications",
        0x8F: "ATI Technologies",
        0x10: "Agere Systems",
        0x91: "NeoMagic",
        0x92: "AuroraNetics",
        0x13: "Golden Empire",
        0x94: "Muskin",
        0x15: "Tioga Technologies",
        0x16: "Netlist",
        0x97: "TeraLogic",
        0x98: "Cicada Semiconductor",
        0x19: "Centon Electronics",
        0x1A: "Tyco Electronics",
        0x9B: "Magis Works",
        0x1C: "Zettacom",
        0x9D: "Cogency Semiconductor",
        0x9E: "Chipcon AS",
        0x1F: "Aspex Technology",
        0x20: "F5 Networks",
        0xA1: "Programmable Silicon Solutions",
        0xA2: "ChipWrights",
        0x23: "Acorn Networks",
        0xA4: "Quicklogic",
        0x25: "Kingmax Semiconductor",
        0x26: "BOPS",
        0xA7: "Flasys",
        0xA8: "BitBlitz Communications",
        0x29: "eMemory Technology",
        0x2A: "Procket Networks",
        0xAB: "Purple Ray",
        0x2C: "Trebia Networks",
        0xAD: "Delta Electronics",
        0xAE: "Onex Communications",
        0x2F: "Ample Communications",
        0xB0: "Memory Experts Intl",
        0x31: "Astute Networks",
        0x32: "Azanda Network Devices",
        0xB3: "Dibcom",
        0x34: "Tekmos",
        0xB5: "API NetWorks",
        0xB6: "Bay Microsystems",
        0x37: "Firecron Ltd",
        0x38: "Resonext Communications",
        0xB9: "Tachys Technologies",
        0xBA: "Equator Technology",
        0x3B: "Concept Computer",
        0xBC: "SILCOM",
        0x3D: "3Dlabs",
        0x3E: "ct Magazine",
        0xBF: "Sanera Systems",
        0x40: "Silicon Packets",
        0xC1: "Viasystems Group",
        0xC2: "Simtek",
        0x43: "Semicon Devices Singapore",
        0xC4: "Satron Handelsges",
        0x45: "Improv Systems",
        0x46: "INDUSYS GmbH",
        0xC7: "Corrent",
        0xC8: "Infrant Technologies",
        0x49: "Ritek Corp",
        0x4A: "empowerTel Networks",
        0xCB: "Hypertec",
        0x4C: "Cavium Networks",
        0xCD: "PLX Technology",
        0xCE: "Massana Design",
        0x4F: "Intrinsity",
        0xD0: "Valence Semiconductor",
        0x51: "Terawave Communications",
        0x52: "IceFyre Semiconductor",
        0xD3: "Primarion",
        0x54: "Picochip Designs Ltd",
        0xD5: "Silverback Systems",
        0xD6: "Jade Star Technologies",
        0x57: "Pijnenburg Securealink",
        0x58: "MemorySolutioN",
        0xD9: "Cambridge Silicon Radio",
        0xDA: "Swissbit",
        0x5B: "Nazomi Communications",
        0xDC: "eWave System",
        0x5D: "Rockwell Collins",
        0x5E: "PAION",
        0xDF: "Alphamosaic Ltd",
        0xE0: "Sandburst",
        0x61: "SiCon Video",
        0x62: "NanoAmp Solutions",
        0xE3: "Ericsson Technology",
        0x64: "PrairieComm",
        0xE5: "Mitac International",
        0xE6: "Layer N Networks",
        0x67: "Atsana Semiconductor",
        0x68: "Allegro Networks",
        0xE9: "Marvell Semiconductors",
        0xEA: "Netergy Microelectronic",
        0x6B: "NVIDIA",
        0xEC: "Internet Machines",
        0x6D: "Peak Electronics",
        0xEF: "Accton Technology",
        0x70: "Teradiant Networks",
        0xF1: "Europe Technologies",
        0xF2: "Cortina Systems",
        0x73: "RAM Components",
        0xF4: "Raqia Networks",
        0x75: "ClearSpeed",
        0x76: "Matsushita Battery",
        0xF7: "Xelerated",
        0xF8: "SimpleTech",
        0x79: "Utron Technology",
        0x7A: "Astec International",
        0xFB: "AVM gmbH",
        0x7C: "Redux Communications",
        0xFD: "Dot Hill Systems",
        0xFE: "TeraChip",
    },
    {
        0x01: "T-RAM Incorporated",
        0x02: "Innovics Wireless",
        0x83: "Teknovus",
        0x04: "KeyEye Communications",
        0x85: "Runcom Technologies",
        0x86: "RedSwitch",
        0x07: "Dotcast",
        0x08: "Silicon Mountain Memory",
        0x89: "Signia Technologies",
        0x8A: "Pixim",
        0x0B: "Galazar Networks",
        0x8C: "White Electronic Designs",
        0x0D: "Patriot Scientific",
        0x0E: "Neoaxiom Corporation",
        0x8F: "3Y Power Technology",
        0x10: "Europe Technologies",
        0x91: "Potentia Power Systems",
        0x92: "C-guys Incorporated",
        0x13: "Digital Communications Technology Incorporated",
        0x94: "Silicon-Based Technology",
        0x15: "Fulcrum Microsystems",
        0x16: "Positivo Informatica Ltd",
        0x97: "XIOtech Corporation",
        0x98: "PortalPlayer",
        0x19: "Zhiying Software",
        0x1A: "Direct2Data",
        0x9B: "Phonex Broadband",
        0x1C: "Skyworks Solutions",
        0x9D: "Entropic Communications",
        0x9E: "Pacific Force Technology",
        0x1F: "Zensys A/S",
        0x20: "Legend Silicon Corp.",
        0xA1: "sci-worx GmbH",
        0xA2: "Oasis Silicon Systems",
        0x23: "Renesas Technology",
        0xA4: "Raza Microelectronics",
        0x25: "Phyworks",
        0x26: "MediaTek",
        0xA7: "Non-cents Productions",
        0xA8: "US Modular",
        0x29: "Wintegra Ltd",
        0x2A: "Mathstar",
        0xAB: "StarCore",
        0x2C: "Oplus Technologies",
        0xAD: "Mindspeed",
        0xAE: "Just Young Computer",
        0x2F: "Radia Communications",
        0xB0: "OCZ",
        0x31: "Emuzed",
        0x32: "LOGIC Devices",
        0xB3: "Inphi Corporation",
        0x34: "Quake Technologies",
        0xB5: "Vixel",
        0xB6: "SolusTek",
        0x37: "Kongsberg Maritime",
        0x38: "Faraday Technology",
        0xB9: "Altium Ltd.",
        0xBA: "Insyte",
        0x3B: "ARM Ltd.",
        0xBC: "DigiVision",
        0x3D: "Vativ Technologies",
        0x3E: "Endicott Interconnect Technologies",
        0xBF: "Pericom",
        0x40: "Bandspeed",
        0xC1: "LeWiz Communications",
        0xC2: "CPU Technology",
        0x43: "Ramaxel Technology",
        0xC4: "DSP Group",
        0x45: "Axis Communications",
        0x46: "Legacy Electronics",
        0xC7: "Chrontel",
        0xC8: "Powerchip Semiconductor",
        0x49: "MobilEye Technologies",
        0x4A: "Excel Semiconductor",
        0xCB: "A-DATA Technology",
        0x4C: "VirtualDigm",
    },
]

memory_types = {
    1: "STD FPM DRAM",
    2: "EDO",
    3: "Pipelined Nibble",
    4: "SDRAM",
    5: "ROM",
    6: "DDR SGRAM",
    7: "DDR SDRAM",
    8: "DDR2 SDRAM",
    9: "DDR2 SDRAM FB-DIMM",
    10: "DDR2 SDRAM FB-DIMM PROBE",
    11: "DDR3 SDRAM",
    12: "DDR4 SDRAM",
}

memory_types_rev = {}
for k, v in memory_types.iteritems():
    memory_types_rev[v] = k

module_types = {
    1: "RDIMM",
    2: "UDIMM",
    3: "SODIMM",
    4: "Micro-DIMM",
    5: "Mini-RDIMM",
    6: "Mini-UDIMM",
}

module_types_rev = {}
for k, v in module_types.iteritems():
    module_types_rev[v] = k


ddr3_module_capacity = {
    0: 256,
    1: 512,
    2: 1024,
    3: 2048,
    4: 4096,
    5: 8192,
    6: 16384,
    7: 32768,
}
ddr3_module_capacity_rev = {}
for k, v in ddr3_module_capacity.iteritems():
    ddr3_module_capacity_rev[v] = k

ddr3_bank_address_bits = {
    0: 3,
    1: 4,
    2: 5,
    3: 6
}
ddr3_bank_address_bits_rev = {}
for k, v in ddr3_bank_address_bits.iteritems():
    ddr3_bank_address_bits_rev[v] = k

ddr3_dev_width = {
    0: 4,
    1: 8,
    2: 16,
    3: 32,
}
ddr3_dev_width_rev = {}
for k, v in ddr3_dev_width.iteritems():
    ddr3_dev_width_rev[v] = k

ddr3_ranks = {
    0: 1,
    1: 2,
    2: 3,
    3: 4
}
ddr3_ranks_rev = {}
for k, v in ddr3_ranks.iteritems():
    ddr3_ranks_rev[v] = k

ddr3_bus_width = {
    0: 8,
    1: 16,
    2: 32,
    3: 64,
}
ddr3_bus_width_rev = {}
for k, v in ddr3_bus_width.iteritems():
    ddr3_bus_width_rev[v] = k

clock_by_freq = {
    400: 800,
    533: 1066,
    667: 1333,
    800: 1600,
    933: 1866,
    1067: 2133
}

tckmin_mtb_125ps_by_clock = {
    800: 0x14,
    1066: 0x0f,
    1333: 0x0c,
    1600: 0x0a,
    1866: 0x09,
    2133: 0x08
}

tckmin_ftb_1ps_by_clock = {
    800: 0x0,
    1066: 0x0,
    1333: 0x0,
    1600: 0x0,
    1866: 0xca,
    2133: 0xc2
}

speed_by_clock = {
    800: 6400,
    1066: 8500,
    1333: 10600,
    1600: 12800,
    1867: 14900,
    2132: 17000,
    2133: 17000,
    2134: 17000,
}

opt_features = {
    "dll-off": 1<<7,
    "rzq/7": 1<<1,
    "rzq/6":1
}

thermal_refresh_opt = {
    "pasr": 1<<7,
    "odts": 1<<3,
    "asr": 1<<2,
    "extended temperature refresh rate": 1<<1,
    "extended temperature range": 1
}

def crc16(data):
    crc = 0
    for b in data:
        crc = crc ^ (int)*ord(b) << 8;
        for i in range(8):
            if (crc & 0x8000):
                crc = crc << 1 ^ 0x1021
            else:
                crc = crc << 1;
    return (crc & 0xFFFF)

def val_mtb_ftb(val, mtb, ftb):
    val_mtb = int(math.ceil(val/mtb))
    val_ftb = 0xff&int(math.ceil((val-val_mtb*mtb)/ftb))
    return val_mtb, val_ftb

def decode_manufacturer(index, mfg):
    index &= 0x7f
    try:
        return jedec_ids[index][mfg]
    except (KeyError, IndexError):
        return 'Unknown ({0}, {1})'.format(index, mfg)


def decode_spd_date(year, week):
    if year == 0 and week == 0:
        return 'Unknown'
    return '20{0:02x}-W{1:x}'.format(year, week)


class SPD(object):
    def __init__(self, bytedata):
        """Parsed memory information

        Parse bytedata input and provide a structured detail about the
        described memory component

        :param bytedata: A bytearray of data to decode
        :return:
        """
        self.rawdata = bytearray(bytedata)
        spd = self.rawdata
        self.info = {'memory_type': memory_types.get(spd[2], 'Unknown')}
        if spd[2] == 11:
            self._decode_ddr3()
        elif spd[2] == 12:
            self._decode_ddr4()

    def _decode_ddr3(self):
        spd = self.rawdata
        finetime = (spd[9] >> 4) / (spd[9] & 0xf)
        fineoffset = spd[34]
        if fineoffset & 0b10000000:
            # Take two's complement for negative offset
            fineoffset = 0 - ((fineoffset ^ 0xff) + 1)
        fineoffset = (finetime * fineoffset) * 10**-3
        mtb = spd[10] / float(spd[11])
        clock = 2 // ((mtb * spd[12] + fineoffset)*10**-3)
        print "clock:", clock
        self.info['speed'] = speed_by_clock.get(clock, 'Unknown')
        self.info['ecc'] = (spd[8] & 0b11000) != 0
        self.info['module_type'] = module_types.get(spd[3] & 0xf, 'Unknown')
        self.info['sdramcap'] = ddr3_module_capacity[spd[4] & 0xf]
        self.info['buswidth'] = ddr3_bus_width[spd[8] & 0b111]
        self.info['sdramwidth'] = ddr3_dev_width[spd[7] & 0b111]
        self.info['ranks'] = ddr3_ranks[(spd[7] & 0b111000) >> 3]
        print "cap=sdramcap/8*buswidth/sdramwidth*ranks"
        self.info['capacity_mb'] = self.info['sdramcap'] / 8 * self.info['buswidth'] / self.info['sdramwidth'] * self.info['ranks']
        print "cap=",self.info['sdramcap'],"/ 8 *",self.info['buswidth'],"/", self.info['sdramwidth'], "*", self.info['ranks'],"=", self.info['capacity_mb']
        self.info['manufacturer'] = decode_manufacturer(spd[117], spd[118])
        self.info['manufacture_location'] = spd[119]
        self.info['manufacture_date'] = decode_spd_date(spd[120], spd[121])
        self.info['serial'] = struct.unpack(
            '>I', struct.pack('4B', *spd[122:126]))[0]
        self.info['model'] = struct.pack('18B', *spd[128:146])

    def mbits_to_sdramcap(self, mbits):
        return ddr3_module_capacity_rev[mbits]

    def __calc_ftb_mtb(self, time, mtb, ftb):
        temp = float(time)/mtb
        remainder = temp % 1
        fine_correction = 1 - remainder
        if remainder == 0:
            return int(temp), 0
        else:
            return int(math.ceil(temp)), int(fine_correction*mtb/ftb)

    def __encode_ddr3_general_section(self):
        bytes_total = 1#256
        crc_cover = 1#bytes 0-125
        spd_bytes_used = 2#176
        B00 = 0xff&(crc_cover<<7 | bytes_total<<4 | spd_bytes_used)

        spd_revision = 0x00
        B01 = spd_revision
        device_type = 0xff&(memory_types_rev["DDR3 SDRAM"])
        B02 = device_type
        module_type = 0xff&(module_types_rev["UDIMM"])
        B03 = module_type

        bits_per_module = self.info["sdramcap"]
        address_bits = ddr3_bank_address_bits_rev[3]
        density_and_banks = 0xff&(address_bits<<4 | bits_per_module)
        B04 = density_and_banks

        rows = 16
        cols = 10
        rows_cols = 0xff&((rows-12)<<3|(cols-9))
        B05 = rows_cols
        
        B06 = 0x00

        ranks = self.info['ranks']
        device_width = self.info['sdramwidth']
        module_organization = 0xff&(ranks<<3 | device_width)
        B07 = module_organization

        ecc = 1
        primary_bus = self.info['buswidth']
        module_memory_bus_width = 0xff&(ecc<<3 | primary_bus)
        B08 = module_memory_bus_width

        ftb_dividend = 1
        ftb_divisor = 1
        ftb = float(ftb_dividend)/float(ftb_divisor)*0.001
        B09 = 0xff&(ftb_dividend<<4 | ftb_divisor)

        mtb_dividend = 1
        mtb_divisor = 8
        mtb = float(mtb_dividend)/float(mtb_divisor)
        B10 = mtb_dividend
        B11 = mtb_divisor

        clock = 1600
        #B12 = tckmin_mtb_125ps_by_clock[clock]
        tckmin = 1.25
        tckmin_mtb, tckmin_ftb = val_mtb_ftb(tckmin, mtb, ftb)
        print "tckmin_mtb:", hex(tckmin_mtb), "tckmin_ftb:", hex(tckmin_ftb)
        B12 = tckmin_mtb
        B13 = 0x00 #reserved
        B14 = 0xfe
        B15 = 0x07

        taa = 13.75
        min_cas_mtb, min_cas_ftb = val_mtb_ftb(taa, mtb, ftb)
        B16 = min_cas_mtb

        twr = 16
        twr_mtb, twr_ftb = val_mtb_ftb(twr, mtb, ftb)
        twr_mtb = int(math.ceil(twr/mtb))
        B17 = twr_mtb

        trcdmin = 13.75
        trcdmin_mtb, trcdmin_ftb = val_mtb_ftb(trcdmin, mtb, ftb)
        B18 = trcdmin_mtb

        trrdmin = max(4*tckmin, 6)
        trrdmin_mtb, trrdmin_ftb = val_mtb_ftb(trrdmin, mtb, ftb)
        B19 = trrdmin_mtb

        trpmin = 13.75
        trpmin_mtb, trpmin_ftb = val_mtb_ftb(trpmin, mtb, ftb)
        B20 = trpmin_mtb

        tras = 35
        tras_mtb, tras_ftb = val_mtb_ftb(tras, mtb, ftb)
        trc = 48.75
        trc_mtb, trc_ftb = val_mtb_ftb(trc, mtb, ftb)

        B21 = 0xff&((trc_mtb>>8)<<4) | (0xff&(tras_mtb>>8))
        B22 = 0xff&(tras_mtb)
        B23 = 0xff&(trc_mtb)

        tdllk = 512*tckmin
        trfc = tdllk
        trfc_mtb, trfc_ftb = val_mtb_ftb(trfc, mtb, ftb)
        
        B24 = 0xff&trfc_mtb
        B25 = 0xff&(trfc_mtb>>8)

        twtr = max(4*tckmin, 7.5)
        twtr_mtb, twtr_ftb = val_mtb_ftb(twtr, mtb, ftb)
        B26 = twtr_mtb

        trtp = max(4*tckmin, 7.5)
        trtp_mtb, trtp_ftb = val_mtb_ftb(trtp, mtb, ftb)
        B27 = trtp_mtb

        tfawmin = 30
        tfawmin_mtb, tfawmin_ftb = val_mtb_ftb(tfawmin, mtb, ftb)
        B28 = 0xff&(tfawmin_mtb>>8)
        B29 = 0xff&(tfawmin_mtb)

        B30 = 0xff&(opt_features["rzq/7"])
        B31 = 0xff&(thermal_refresh_opt["pasr"] | thermal_refresh_opt["odts"] | thermal_refresh_opt["asr"])

        B32 = 0x00

        B33 = 0x00
        B34 = tckmin_ftb
        B35 = min_cas_ftb
        B36 = trcdmin_ftb
        B37 = trpmin_ftb
        B38 = trc_ftb
        B39 = 0x00 #res
        B40 = 0x00 #res
        B41 = 0x00 # untested MAC
        B42 = 0x00 #res
        B43 = 0x00 #res
        B44 = 0x00 #res
        B45 = 0x00 #res
        B46 = 0x00 #res
        B47 = 0x00 #res
        B48 = 0x00 #res
        B49 = 0x00 #res
        B50 = 0x00 #res
        B51 = 0x00 #res
        B52 = 0x00 #res
        B53 = 0x00 #res
        B54 = 0x00 #res
        B55 = 0x00 #res
        B56 = 0x00 #res
        B57 = 0x00 #res
        B58 = 0x00 #res
        B59 = 0x00 #res
        
        data = [B00, B01, B02, B03, B04, B05, B06, B07,
                B08, B09, B10, B11, B12, B13, B14, B15,
                B16, B17, B18, B19, B20, B21, B22, B23,
                B24, B25, B26, B27, B28, B29, B30, B31,
                B32, B33, B34, B35, B36, B37, B38, B39,
                B40, B41, B42, B43, B44, B45, B46, B47,
                B48, B49, B50, B51, B52, B53, B54, B55,
                B56, B57, B58, B59]
        return data
                       
    def encode_ddr3(self):
        data = self.__encode_ddr3_general_section()
        # bits_per_module = 4096*1024*1024
        # address_bits = 0 # means 8 banks I think
        # density_and_banks = 0xff&(address_bits<<4 | int(math.log(bits_per_module, 2))-28)
        # rows = 16
        # cols = 10
        # rows_cols = 0xff&((rows-12)<<3|(cols-9))
        
        # ranks_dqs = 0xff&(self.info['ranks']<<3 | self.info['sdramwidth'])
        # ecc_bus_width = 0xff & (0<<3 | (int(math.log(64, 2)) - 3))
        # fine_timebase_dividend_divisor = 0x52
        # medium_timebase_dividend = 0x01
        # medium_timebase_divisor = 0x08
        # minimum_sdram_cycle = 0x0f
        # cas_latency1 = 0xfe
        # cas_latency2 = 0x07
        # minimum_cas_latency = 0x69
        # minimum_write_recovery_time = 0x78
        # ras_to_cas = 0x69
        # ra_to_ra = 0x3c
        # precharge_delay = 0x69
        # rasmin=0x12c
        # rcmin=0x1a4
        # rfcmin = 0x370
        # wtrmin = 0x3c
        # rtpmin = 0x3c
        # fawmin = 0x12c
        # sdram_optional_features = 1<<1
        # sdram_thermal_refresh = 1<<7 | 1<<3
        
        # data = [0x92, 0x00, memory_types_rev["DDR3 SDRAM"],
        #         module_types_rev["UDIMM"], density_and_banks, rows_cols,
        #         0x00, ranks_dqs, ecc_bus_width,
        #         fine_timebase_dividend_divisor, medium_timebase_dividend, medium_timebase_divisor,
        #         minimum_sdram_cycle, 0x00, cas_latency1,
        #         cas_latency2, minimum_cas_latency, minimum_write_recovery_time,
        #         ras_to_cas, ra_to_ra, precharge_delay,
        #         0xff&((rasmin>>8)<<4 | rcmin>>8), 0xff&rasmin, 0xff&rcmin,
        #         0xff&(rfcmin), 0xff&(rfcmin>>8), wtrmin,
        #         rtpmin, 0xff&(fawmin>>8), 0xff&(fawmin),
        #         sdram_optional_features, sdram_thermal_refresh, 0x00,
        #         0x00, 0x00, 0x00,
        #         0x00, 0x00, 0x00,#38
        #         0x00, 0x00, 0x00,#41
        #         0x00, 0x00, 0x00,#44
        #         0x00, 0x00, 0x00,#47
        #         0x00, 0x00, 0x00,#50
        #         0x00, 0x00, 0x00,
        #         0x00, 0x00, 0x00,
        #         0x00, 0x00, 0x00,#59

        data += [0x0f, 0x11, 0x1f,
                0x00, 0x00, 0x00,#65
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,#116
                0x03, 0x0b, 0x00,
                0x00, 0x00, 0x00,#122
                0x00, 0x00, 0x00,#125
                0x00, 0x00, ord('t'),#128
                ord('-'), ord('o'), ord('c'),#131
                ord('t'), ord('0'), ord('0'),#134
                ord('0'), ord('0'), ord('0'),#137
                ord('0'), ord('0'), ord('0'),#140
                ord('0'), ord('0'), ord('0'),#143
                ord('0'), ord('1'), 0x00,#146
                0x02, 0x03, 0x0b, #149
                0x00, 0x00, 0x00,#152
                0x00, 0x00, 0x00,#155
                0x00, 0x00, 0x00,#158
                0x00, 0x00, 0x00,#161
                0x00, 0x00, 0x00,#164
                0x00, 0x00, 0x00,#167
                0x00, 0x00, 0x00,#170
                0x00, 0x00, 0x00,#173
                0x00, 0x00]
        out = ""
        for b in data:
            out+=chr(b)
        return out

    def _decode_ddr4(self):
        spd = self.rawdata
        if spd[17] == 0:
            fineoffset = spd[125]
            if fineoffset & 0b10000000:
                fineoffset = 0 - ((fineoffset ^ 0xff) + 1)
            clock = 2 // ((0.125 * spd[18] + fineoffset * 0.001) * 0.001)
            self.info['speed'] = speed_by_clock.get(clock, 'Unknown')
        else:
            self.info['speed'] = 'Unknown'
        self.info['ecc'] = (spd[13] & 0b11000) == 0b1000
        self.info['module_type'] = module_types.get(spd[3] & 0xf,
                                                    'Unknown')
        sdramcap = ddr3_module_capacity[spd[4] & 0xf]
        buswidth = ddr3_bus_width[spd[13] & 0b111]
        sdramwidth = ddr3_dev_width[spd[12] & 0b111]
        ranks = ddr3_ranks[(spd[12] & 0b111000) >> 3]
        self.info['capacity_mb'] = sdramcap / 8 * buswidth / sdramwidth * ranks
        self.info['manufacturer'] = decode_manufacturer(spd[320], spd[321])
        self.info['manufacture_location'] = spd[322]
        self.info['manufacture_date'] = decode_spd_date(spd[323], spd[324])
        self.info['serial'] = struct.unpack(
            '>I', struct.pack('4B', *spd[325:329]))[0]
        self.info['model'] = struct.pack('18B', *spd[329:347])
