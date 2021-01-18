#!/usr/bin/env python3

# Copyright (C) 2020-2021 Gabriele Bozzola
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


"""Plot the multipolar decomposition of Psi4 as measured by a given detector
and a given l and m.
"""

if __name__ == "__main__":
    setup_matplotlib()

    desc = __doc__

    parser = pah.init_argparse(desc)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "--detector-num",
        type=int,
        required=True,
        help="Number of the spherical surface over which to read Psi4",
    )

    parser.add_argument(
        "--mult-l", type=int, default=2, help="Multipole number l"
    )
    parser.add_argument(
        "--mult-m", type=int, default=2, help="Multipole number m"
    )

    args = pah.get_args(parser)

    # Parse arguments

    if args.figname is None:
        figname = f"Psi4_{args.mult_l}{args.mult_m}_det{args.detector_num}"
    else:
        figname = args.figname

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    sim = SimDir(args.datadir)
    reader = sim.gravitationalwaves

    radius = reader.radii[args.detector_num]
    detector = reader[radius]

    if (args.mult_l, args.mult_m) not in detector.available_lm:
        logger.debug(f"Available multipoles {detector.available_lm}")
        raise ValueError(
            f"Multipole {args.mult_l}, {args.mult_m} not available"
        )

    psi4 = detector[args.mult_l, args.mult_m]

    logger.debug(f"Plotting Psi4")

    plt.plot(psi4.real(), label=fr"$\Re \Psi_4^{{{args.mult_l}{args.mult_l}}}$")
    plt.plot(psi4.imag(), label=fr"$\Im \Psi_4^{{{args.mult_l}{args.mult_l}}}$")

    plt.legend()
    plt.xlabel("Time")
    plt.ylabel(r"$r \Psi_4$")

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
