# Example executables build with `kuibit`

In this directory, we collect working programs built with `kuibit`. You can use
these scripts as good examples of ``kuibit`` usage (or you can directly use
them).

> :warning: While `kuibit` is tested at each commit to ensure that nothing
>           breaks, these scripts are not. If you find a script that does not
>           work, please report it and we will fix that.

Scripts available:
- `plot_grid_var`, plot any 2D grid function on a grid specified via
  command-line.
- `plot_scalar`, plot any reduction of any variable as a time series.
- `plot_1d_vars`, plot one or more along a 1D axis.
- `plot_1d_vars`, plot one or more along a 1D axis.
- `plot_ah_trajectories`, plot the trajectories of given apparent horizons (in
  3D or a projection on a plane).
- `plot_ah_separation`, plot the coordinate separation between the centroids of
  two given apparent horizons.
- `plot_constraints`, plot the absolute value of the violation of the
  constraints over time.
- `plot_psi4`, plot Psi4 as measured at a given distance.
- `plot_psi4`, plot the computational speed as measured by Carpet's
  `physical_time_per_hour`.
- `plot_gw_energy`, plot the instantaneous power and cumulative energy lost via
   gravitational waves as measured at a given distance.
- `print_available_timeseries`, prints the list of timeseries that can `kuibit`
  can access.
- `print_available_iterations`, prints the list of iterations available for a given
  variable.
