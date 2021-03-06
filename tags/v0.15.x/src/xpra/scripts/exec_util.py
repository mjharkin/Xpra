# This file is part of Xpra.
# Copyright (C) 2012-2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import subprocess

from xpra.util import nonl
from xpra.log import Logger
log = Logger("util")

def safe_exec(cmd, stdin=None, log_errors=True, **kwargs):
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    out, err = process.communicate(stdin)
    code = process.poll()
    l=log.debug
    if code!=0 and log_errors:
        l=log.error
    l("signal_safe_exec(%s, %s, %s) stdout='%s'", cmd, stdin, kwargs, nonl(out))
    l("signal_safe_exec(%s, %s, %s) stderr='%s'", cmd, stdin, kwargs, nonl(err))
    return  code, out, err
