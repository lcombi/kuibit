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
from kuibit.visualize_matplotlib import (
    setup_matplotlib,
    plot_color,
    add_text_to_figure_corner,
    save,
)


"""This script plots one or more grid functions along a 1D axis with options
specified via command-line. """

if __name__ == "__main__":
    setup_matplotlib()

    desc = """Plot one or more 1D grid functions as output by Carpet."""

    parser = pah.init_argparse(desc)
    pah.add_grid_to_parser(parser)
    pah.add_figure_to_parser(parser)

    parser.add_argument(
        "--variables",
        type=str,
        required=True,
        help="Variables to plot",
        nargs="+",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=-1,
        help="Iteration to plot. If -1, the latest.",
    )
    parser.add(
        "--logscale", help="Use a logarithmic y scale.", action="store_true"
    )
    parser.add(
        "--vmin",
        help=(
            "Minimum value of the variable. "
            "If logscale is True, this has to be the log."
        ),
        type=float,
    )
    parser.add(
        "--vmax",
        help=(
            "Maximum value of the variable. "
            "If logscale is True, this has to be the log."
        ),
        type=float,
    )
    parser.add(
        "--xmin",
        help=("Minimum coordinate."),
        type=float,
    )
    parser.add(
        "--xmax",
        help=("Maximum coordinate."),
        type=float,
    )
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Whether to take the absolute value.",
    )
    parser.add_argument(
        "--axis",
        type=str,
        choices=["x", "y", "z"],
        default="x",
        help="Axis to plot (default: %(default)s)",
    )
    args = pah.get_args(parser)

    # Parse arguments

    iteration = args.iteration

    if args.figname is None:
        var_names = "_".join(args.variables)
        figname = f"{var_names}_{args.axis}"
    else:
        figname = args.figname

    logger = logging.getLogger(__name__)

    if args.verbose:
        logging.basicConfig(format="%(asctime)s - %(message)s")
        logger.setLevel(logging.DEBUG)

    sim = SimDir(args.datadir)
    reader = sim.gridfunctions[args.axis]

    for var in args.variables:
        if var not in reader:
            raise ValueError(f"{var} is not available")

    for variable in args.variables:

        logger.debug(f"Reading variable {variable}")
        logger.debug(f"Variables available {reader}")
        var = reader[variable]
        logger.debug(f"Read variable {variable}")

        if iteration == -1:
            iteration = var.available_iterations[-1]

        time = var.time_at_iteration(iteration)

        logger.debug(f"Using iteration {iteration} (time = {time})")

        if args.absolute:
            data = abs(var[iteration])
            variable_name = f"abs({variable})"
        else:
            data = var[iteration]
            variable_name = variable

        logger.debug(f"Merging refinement levels")
        data = data.merge_refinement_levels()

        if args.logscale:
            label = f"log10({variable_name})"
            data = data.log10()
        else:
            label = variable_name

        logger.debug(f"Using label {label}")

        logger.debug(f"Plotting variable {variable}")

        plt.plot(data.coordinates_from_grid()[0], data.data_xyz, label=label)

    add_text_to_figure_corner(fr"$t = {time:.3f}$")

    plt.legend()
    plt.xlabel(args.axis)
    plt.ylim(ymin=args.vmin, ymax=args.vmax)
    plt.xlim(xmin=args.xmin, xmax=args.xmax)

    output_path = os.path.join(args.outdir, figname)
    logger.debug(f"Saving in {output_path}")
    plt.tight_layout()
    save(output_path, args.fig_extension, as_tikz=args.as_tikz)
