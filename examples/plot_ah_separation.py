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

"""Plot the coordinate separation of two centroids of the two given apparent
horizons. """

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "-a",
        "--horizons",
        type=int,
        required=True,
        help="Apparent horizons to plot",
        nargs=2,
    )

    args = pah.get_args(parser)

    # Parse arguments

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    if args.figname is None:
        horizons = "_".join([str(h) for h in args.horizons])
        figname = f"ah_{horizons}_separation"
    else:
        figname = args.figname

    logger.debug(f"Figname: {figname}")

    sim = SimDir(args.datadir)
    sim_hor = sim.horizons

    logger.debug(
        f"Apparent horizons available: {sim_hor.available_apparent_horizons}"
    )

    # Check that the horizons are available
    for ah in args.horizons:
        if ah not in sim_hor.available_apparent_horizons:
            raise ValueError(f"Apparent horizons {ah} is not available")

    logger.debug(f"Reading horizons and computing separation")
    # We can use any index for the qlm index, it will be thrown away
    ah1 = sim_hor[0, args.horizons[0]].ah
    ah2 = sim_hor[0, args.horizons[1]].ah

    separation = (
        (ah1.centroid_x - ah2.centroid_x) ** 2
        + (ah1.centroid_y - ah2.centroid_y) ** 2
        + (ah1.centroid_z - ah2.centroid_z) ** 2
    ).sqrt()

    # Plot
    plt.ylabel("Separation")
    plt.xlabel("Time")
    plt.plot(separation)

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
