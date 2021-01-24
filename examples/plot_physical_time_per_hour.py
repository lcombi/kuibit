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
from kuibit.visualize_matplotlib import (
    setup_matplotlib,
    save,
)


"""Plot how much physical time is being simulated per walltime hour.
"""

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    args = pah.get_args(parser)

    # Parse arguments

    if args.figname is None:
        figname = f"physical_time_per_hour"
    else:
        figname = args.figname

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    sim = SimDir(args.datadir)


    if "physical_time_per_hour" not in sim.ts.scalar:
        raise ValueError(
            "physical_time_per_hour not available"
        )

    phys_time = sim.ts.scalar['physical_time_per_hour']

    logger.debug(f"Plotting physical_time_per_hour")

    plt.plot(phys_time)

    plt.xlabel("Simulation Time")
    plt.ylabel(r"Simulated physical time per hour")

    plt.twinx()

    plt.plot(phys_time * 24)
    plt.ylabel(r"Simulated physical time per day")

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
