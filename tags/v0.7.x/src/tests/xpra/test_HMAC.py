#!/usr/bin/env python
# This file is part of Parti.
# Copyright (C) 2011, 2012 Antoine Martin <antoine@nagafix.co.uk>
# Parti is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import hmac

def main():
    password = "71051d81d27745b59c1c56c6e9046c19697e452453e04aa5abbd52c8edc8c232"
    salt = "99ea464f-7117-4e38-95b3-d3aa80e7b806"
    hmac_hash = hmac.HMAC(password, salt)
    print("hash(%s,%s)=%s" % (password, salt, hmac_hash))
    print("hex(hash)=%s" % hmac_hash.hexdigest())
    assert hmac_hash.hexdigest()=="dc26a074c9378b1b5735a27563320a26"


if __name__ == "__main__":
    main()
