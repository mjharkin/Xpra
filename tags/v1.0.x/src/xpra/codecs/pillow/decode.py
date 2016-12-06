# This file is part of Xpra.
# Copyright (C) 2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.log import Logger
log = Logger("encoder", "pillow")

import PIL                      #@UnresolvedImport
from PIL import Image           #@UnresolvedImport
from xpra.codecs.pillow import PIL_VERSION


def get_version():
    return PIL_VERSION

def get_type():
    return "pillow"

def do_get_encodings():
    log("PIL.Image.OPEN=%s", Image.OPEN)
    encodings = []
    for encoding in ["png", "png/L", "png/P", "jpeg"]:
        #strip suffix (so "png/L" -> "png")
        stripped = encoding.split("/")[0].upper()
        if stripped in Image.OPEN:
            encodings.append(encoding)
    log("do_get_encodings()=%s", encodings)
    return encodings

def get_encodings():
    return ENCODINGS

ENCODINGS = do_get_encodings()

def get_info():
    return  {
            "version"       : get_version(),
            "encodings"     : get_encodings(),
            }

def selftest(full=False):
    global ENCODINGS
    import binascii
    from xpra.os_util import BytesIOClass
    #test data generated using the encoder:
    for encoding, hexdata in (
                       ('png',      "89504e470d0a1a0a0000000d4948445200000020000000200806000000737a7af40000002849444154785eedd08100000000c3a0f9531fe4855061c0800103060c183060c0800103060cbc0f0c102000013337932a0000000049454e44ae426082"),
                       ('png',      "89504e470d0a1a0a0000000d4948445200000020000000200802000000fc18eda30000002549444154785eedd03101000000c2a0f54fed610d884061c0800103060c183060c080810f0c0c20000174754ae90000000049454e44ae426082"),
                       ('png/L',    "89504e470d0a1a0a0000000d4948445200000020000000200800000000561125280000000274524e5300ff5b9122b50000002049444154785e63fccf801f3011906718550009a1d170180d07e4bc323cd20300a33d013f95f841e70000000049454e44ae426082"),
                       ('png/L',    "89504e470d0a1a0a0000000d4948445200000020000000200800000000561125280000001549444154785e63601805a321301a02a321803d0400042000017854be5c0000000049454e44ae426082"),
                       ('png/P',    "89504e470d0a1a0a0000000d494844520000002000000020080300000044a48ac600000300504c5445000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000b330f4880000010074524e53ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0053f707250000001c49444154785e63f84f00308c2a0087c068384012c268388ca87000003f68fc2e077ed1070000000049454e44ae426082"),
                       ('png/P',    "89504e470d0a1a0a0000000d494844520000002000000020080300000044a48ac600000300504c5445000000000000000000000000000000000000000000000000000000000000000000330000660000990000cc0000ff0000003300333300663300993300cc3300ff3300006600336600666600996600cc6600ff6600009900339900669900999900cc9900ff990000cc0033cc0066cc0099cc00cccc00ffcc0000ff0033ff0066ff0099ff00ccff00ffff00000033330033660033990033cc0033ff0033003333333333663333993333cc3333ff3333006633336633666633996633cc6633ff6633009933339933669933999933cc9933ff993300cc3333cc3366cc3399cc33cccc33ffcc3300ff3333ff3366ff3399ff33ccff33ffff33000066330066660066990066cc0066ff0066003366333366663366993366cc3366ff3366006666336666666666996666cc6666ff6666009966339966669966999966cc9966ff996600cc6633cc6666cc6699cc66cccc66ffcc6600ff6633ff6666ff6699ff66ccff66ffff66000099330099660099990099cc0099ff0099003399333399663399993399cc3399ff3399006699336699666699996699cc6699ff6699009999339999669999999999cc9999ff999900cc9933cc9966cc9999cc99cccc99ffcc9900ff9933ff9966ff9999ff99ccff99ffff990000cc3300cc6600cc9900cccc00ccff00cc0033cc3333cc6633cc9933cccc33ccff33cc0066cc3366cc6666cc9966cccc66ccff66cc0099cc3399cc6699cc9999cccc99ccff99cc00cccc33cccc66cccc99ccccccccccffcccc00ffcc33ffcc66ffcc99ffccccffccffffcc0000ff3300ff6600ff9900ffcc00ffff00ff0033ff3333ff6633ff9933ffcc33ffff33ff0066ff3366ff6666ff9966ffcc66ffff66ff0099ff3399ff6699ff9999ffcc99ffff99ff00ccff33ccff66ccff99ccffccccffffccff00ffff33ffff66ffff99ffffccffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000023faca40000001549444154785e63601805a321301a02a321803d0400042000017854be5c0000000049454e44ae426082"),
                       ('jpeg',     "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e1211101318281a181616183123251d283a333d3c3933383740485c4e404457453738506d51575f626768673e4d71797064785c656763ffdb0043011112121815182f1a1a2f634238426363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363ffc00011080020002003012200021101031101ffc4001500010100000000000000000000000000000007ffc40014100100000000000000000000000000000000ffc40014010100000000000000000000000000000000ffc40014110100000000000000000000000000000000ffda000c03010002110311003f009f800000000000ffd9"),
                       ('jpeg',     "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e1211101318281a181616183123251d283a333d3c3933383740485c4e404457453738506d51575f626768673e4d71797064785c656763ffdb0043011112121815182f1a1a2f634238426363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363ffc00011080020002003012200021101031101ffc4001500010100000000000000000000000000000007ffc40014100100000000000000000000000000000000ffc40014010100000000000000000000000000000000ffc40014110100000000000000000000000000000000ffda000c03010002110311003f009f800000000000ffd9"),
                       ('webp',     "524946465c00000057454250565038580a000000100000001f00001f0000414c50480f00000001071011110012c2ffef7a44ff530f005650382026000000d002009d012a200020003ed162aa4fa825a3a2280801001a096900003da3a000fef39d800000"),
                       ('webp',     "524946465c00000057454250565038580a000000100000001f00001f0000414c50480f00000001071011110012c2ffef7a44ff530f005650382026000000d002009d012a200020003ed162aa4fa825a3a2280801001a096900003da3a000fef39d800000"),
                       ):
        if encoding not in ENCODINGS:
            #removed already
            continue
        try:
            cdata = binascii.unhexlify(hexdata)
            buf = BytesIOClass(cdata)
            img = PIL.Image.open(buf)
            assert img, "failed to open image data"
            data_fn = getattr(img, "tobytes", getattr(img, "tostring", None))
            raw_data = data_fn("raw", img.mode)
            assert raw_data
            #now try with junk:
            cdata = binascii.unhexlify("ABCD"+hexdata)
            buf = BytesIOClass(cdata)
            try:
                img = PIL.Image.open(buf)
                log.warn("Pillow failed to generate an error parsing invalid input")
            except Exception as e:
                log("correctly raised exception for invalid input: %s", e)
        except Exception as e:
            try:
                #py2k:
                datainfo = cdata.encode("string_escape")
            except:
                try:
                    datainfo = cdata.encode("unicode_escape").decode()
                except:
                    datainfo = str(hexdata)
            log.warn("Pillow error decoding %s with data=%s..", encoding, datainfo[:16])
            log.warn(" %s", e, exc_info=True)
            ENCODINGS.remove(encoding)
