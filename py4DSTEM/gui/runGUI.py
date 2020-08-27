#!/usr/bin/env python

import py4DSTEM
from py4DSTEM.gui import DataViewer
import sys

def launch():
    app = py4DSTEM.gui.DataViewer(sys.argv)

    sys.exit(app.exec_())

if __name__ == '__main__':
    app = py4DSTEM.gui.DataViewer(sys.argv)

    sys.exit(app.exec_())
