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
import os

import matplotlib.pyplot as plt

from kuibit.simdir import SimDir
from kuibit import argparse_helper as pah
from kuibit.visualize import (
    setup_matplotlib,
    save,
)

"""Plot the absolute value of the constraints violation (max and norm2). """

# TODO: It would be very easy to extend this code to use take the list of
#       reductions form command-line

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)
    args = pah.get_args(parser)

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    sim = SimDir(args.datadir)
    reader = sim.timeseries
    logger.debug(f"Variables available {reader}")

    def plot_constraint(constraint, reduction):
        logger.debug(f"Reading {reduction} of {constraint}")
        var = reader[reduction][constraint]
        logger.debug(f"Read {reduction} of {constraint}")
        plt.semilogy(abs(var), label=f"{reduction}(|{constraint}|)")
        logger.debug(f"Plotted {reduction} of {constraint}")

    for reduction in ["max", "norm2"]:
        logger.debug(f"Working with reduction: {reduction}")

        plt.clf()

        if args.figname is None:
            figname = f"constraints_{reduction}"
        else:
            figname = args.figname + f"_{reduction}"

        # We have multiple choices depending on the code used to
        # compute the constraint
        constraint_names = [
            ["H", "M1", "M2", "M3"],  # McLachlan
            ["hc", "mc", "my", "mz"],  # Lean
            ["hamc", "momcx", "momxy", "momcz", "divE"],  # ProcaConstraints
        ]

        for names in constraint_names:
            for constraint in names:
                if constraint in reader[reduction]:
                    plot_constraint(constraint, reduction)

        plt.legend()
        output_path = os.path.join(args.outdir, figname)
        logger.debug(f"Saving in {output_path}")
        save(output_path, args.fig_extension, as_tikz=args.as_tikz)
