#!/usr/bin/env python3

# Copyright (C) 2021 Gabriele Bozzola
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <https://www.gnu.org/licenses/>.

import logging

from kuibit.simdir import SimDir
from kuibit import argparse_helper as pah

"""Print the list of timeseries available to kuibit."""

if __name__ == "__main__":

    desc = __doc__
    parser = pah.init_argparse(desc)
    args = pah.get_args(parser)
    print(SimDir(args.datadir).timeseries)
