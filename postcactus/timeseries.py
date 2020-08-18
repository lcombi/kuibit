#!/usr/bin/env python3
"""The :py:mod:`~.timeseries` module provides a representation of time series
and convenience functions to create timeseries.

"""

import numpy as np
from scipy import signal
from postcactus.series import BaseSeries
from postcactus import frequencyseries


def remove_duplicate_iters(t, y):
    """Remove overlapping segments from a time series in (t,y).

    Only the latest of overlapping segments is kept, the rest
    removed.

    This function is used for cleaning up simulations with multiple
    checkpoints.

    Note, if t = [1, 2, 3, 4, 2, 3] the output will be [1, 2, 3].
    The '4' is discarded because it is not the last segment. The
    idea is that if this corresponds to a simulation restart, you
    may have changed the paramters, so that 4 is not anymore correct.
    We consider the second restart the "truth".

    :param t:  Times
    :type t:   1D numpy array
    :param y:  Values
    :type t:   1D numpy array

    :returns:  Strictly monotonic time series
    :rtype:    :py:class:`~.TimeSeries`

    """
    # Let's unpack this code.
    # First, we define a new variable t2.
    #
    # t2 is essentially the "cumulative minimum" of the times of the time
    # series: t2[i] is the minimum up to index i
    #
    # To be more specific, we walk the time array backwards (t[::-1]) and
    # we compute the cumulative minima. Then, we reverse the array ([::-1])
    #
    # For example, if t = [1, 2, 3, 4, 2, 3]
    # Then t[::-1] = [3, 2, 4, 3, 2, 1], and
    # np.minimum.accumulate(t[::-1]) = [3, 2, 2, 2, 2, 1]
    # Reversing it: t2 = [1, 2, 2, 2, 2, 3]
    #
    # If t had no nuplicates t2 and t would be the same.
    # When t has duplicates, t2 is like t but in place of the duplicates
    # it has values that are equal or smaller.
    #
    # What we want is to have as output [1, 2, 3]
    # To get that, we compare t and t2. Values that are not duplicated
    # are those subtracted with the following are positive.
    # (t[:-1] < t2[1:])

    # First, we make sure that we are dealing with arrays and not lists
    t = np.array(t)
    y = np.array(y)

    t2 = np.minimum.accumulate(t[::-1])[::-1]
    # Here we append [True] because the last point is always included
    msk = np.hstack((t[:-1] < t2[1:], [True]))

    return TimeSeries(t[msk], y[msk])


def unfold_phase(phase):
    """Remove phase jumps to get a continous (unfolded) phase.

    :param phase:     Phase
    :type phase:      1D numpy array

    :returns:         Phase plus multiples of pi chosen to minimize jumps
    :rtype:           1D numpy array
    """
    # TODO: This function should be generalized to allow arbitary jumps.
    #       This is trivially done by adding an argument jump with default
    #       value of 2 pi.

    # nph is how many time we reach 2 pi
    nph = phase / (2 * np.pi)
    # wind is the winding number, how many time we have went over 2 * np.pi
    wind = np.zeros_like(phase)
    # wind[0] = 0. Then, we find the jumps, when the phase goes from 2 pi to 0
    # (or anything with the same offset). Since we divided by 2 pi, a jump is
    # when nph goes from 1 to 0. np.rint allows us to identify the offest of 2
    # pi: when the difference between phase[:-1] - phase[1:] is greater than 2
    # pi, this will be rounded up to 1, when it is smaller, it is rounded down
    # to 0. For example, if phase[i] = np.pi + eps and phase[i+1] = -np.pi,
    # then, this is a jump and np.rint rounds to 1.
    wind[1:] = np.rint(nph[:-1] - nph[1:])
    # Finally, we collect how many jumps have occurred. This is the winding
    # number and tell us how many 2 pi we have to add.
    wind = np.cumsum(wind)
    return phase + (2 * np.pi) * wind


def combine_ts(series, prefer_late=True):
    """Combine several overlapping time series into one.

    In intervals covered by two or more time series, which data is used depends
    on the parameter prefer_late. If two segments start at the same time, the
    longer one gets used.

    :param series: The timeseries to combine
    :type series:  list of :py:class:`~.TimeSeries`
    :param prefer_late: Prefer data that starts later for overlapping segments
    :type prfer_late:   bool

    :returns:      The combined time series
    :rtype:        :py:class:`~.TimeSeries`

    """

    # Late and early can be implemented in one shot by implementing one and
    # sending t -> -t for the other. For the "straight" way we implement
    # combine_ts_early.
    #
    # Let's consider a simple example for the reversed case
    # t1 = [1, 2, 3], t2 = [2, 3, 4], we want to have t = [1, 2, 3, 4]
    # sign = -1
    # timeseries = [t2, t1]
    # times = t2[::-1] = [4, 3, 2]
    # Next we walk through the remaining elements of the list
    # We want only to keep those with t < times[-1] = 2 (hence the switch)
    # In this case msk = [3, 2, 1] < 2 = [False, False, True], so
    # s_t[msk] = [1] and times = [4, 3, 2, 1].
    # At the end, we need to reverse the order again

    # sign is responsible of inverting the sorting key
    sign = -1 if prefer_late else 1

    # Tuples are compared lexicographically; the first items are compared; if
    # they are the same then the second items are compared, and so on.
    # So here we sort by tmin and tmax
    timeseries = sorted(series,
                        key=lambda x: (sign * x.tmin, sign * x.tmax))
    # Now we are going to build up the t and y array, starting with the first
    times = timeseries[0].t[::sign]
    values = timeseries[0].y[::sign]
    for s in timeseries[1:]:
        # We need to walk backwards for "prefer_late"
        s_t = s.t[::sign]
        s_y = s.y[::sign]
        # We only keep those times that we don't have yet in the array times
        msk = s_t < times[-1] if prefer_late else s_t > times[-1]
        times = np.append(times, s_t[msk])
        values = np.append(values, s_y[msk])

    return TimeSeries(times[::sign], values[::sign])


def sample_common(series):
    """Resample a list of timeseries to the largest time interval covered
    by all timeseries, using regularly spaced time.

    The number of sample points is the minimum over all time series.

    :param ts: The timeseries to resample
    :type ts:  List of :py:class:`~.TimeSeries`

    :returns:  Resampled time series so that they are all defined in
               the same interval
    :rtype:    List of :py:class:`~.TimeSeries`

    """
    # Find the series with max tmin
    s_tmin = max(series, key=lambda x: x.tmin)
    # Find the series with min tmax
    s_tmax = min(series, key=lambda x: x.tmax)
    # Find the series with min number of points
    s_ns = min(series, key=len)
    t = np.linspace(s_tmin.tmin, s_tmax.tmax, len(s_ns))
    return [s.resampled(t) for s in series]


class TimeSeries(BaseSeries):
    """This class represents real or complex valued time series.

    TimeSeries are defined providing a time list or array and the corresponding
    values. For example,

    .. code-block:: python

        times = np.linspace(0, 2 * np.pi, 100)
        values = np.sin(times)

        ts = TimeSeries(times, values)


    Times cannot be empty or not monotonically increasing.
    Times and values must have the same length.

    TimeSeries are well-behaved classed, many operations and methods are
    implemented. For instance, you can sum/multiply two Timeseries.

    numpy acts on TimeSeries cleanly, eg. ``np.log10(TimeSeries)`` is a
    TimeSeries with ``log10(data)``.

    TimeSeries have methods for smoothing, windowing, extracting phase and
    more.

    :ivar t:   Times
    :vartype t: 1D numpy array or float
    :ivar y:   Values
    :vartype y: 1D numpy array or float

    :ivar spline_real: Coefficients for a spline represent of the real part
                       of y
    :vartype spline_real: Tuple

    :ivar spline_imag: Coefficients for a spline represent of the real part
                       of y
    :vartype spline_imag: Tuple

    """

    # NOTE: Are you adding a function? Document it in timeseries.rst!

    def __init__(self, t, y):
        """Constructor.

        :param t: Sampling times, need to be strictly increasing
        :type t:  1D numpy array or list

        :param y: Data samples, can be real or complex valued
        :type y:  1D numpy array or list

        """
        # First, let's check if we have a scalar as input
        # In that case, we turn it into an array

        if (hasattr(y, '__len__')):
            if (len(t) > 1):
                # Make sure that it is an array (it could be a list)
                t_array = np.array(t)

                # Example:
                # self.t = [1,2,3]
                # self.t[1:] = [2, 3]
                # self.t[:-1] = [1, 2]
                # dt = [1,1]
                dt = t_array[1:] - t_array[:-1]
                if (dt.min() <= 0):
                    raise ValueError('Time not monotonically increasing')

        # Use BaseClass init
        super().__init__(t, y)

    # The following are the setters and getters, so that we can "resolve" .t
    # and .y

    @property
    def t(self):
        # This is defined BaseClass
        return self.data_x

    @t.setter
    def t(self, t):
        # This is defined BaseClass
        self.data_x = t

    @property
    def y(self):
        # This is defined BaseClass
        return self.data_y

    @y.setter
    def y(self, y):
        # This is defined BaseClass
        self.data_y = y

    @property
    def tmin(self):
        """Return the starting time.

        :returns:  Initial time of the timeseries
        :rtype:    float
        """
        return self.t[0]

    @property
    def tmax(self):
        """Return the final time.

        :returns:  Final time of the timeseries
        :rtype:    float
        """
        return self.t[-1]

    @property
    def dt(self):
        """Return the delta t if the series is regularly sampled,
        otherwise raise error.

        :returns: Delta t
        :rtype: float

        """
        dt = self.t[1:] - self.t[:-1]
        dt0 = dt[0]

        if (not np.allclose(dt, dt0)):
            raise ValueError("Timeseries is not regularly sampled")

        return dt0

    @property
    def time_length(self):
        """Return the length of the covered time interval.

        :returns:  Length of time covered by the timeseries (tmax - tmin)
        :rtype:    float
        """
        return self.tmax - self.tmin

    def regular_resampled(self):
        """Return a new timeseries resampled to regularly spaced times,
        with the
        same number of points.

        :returns: Regularly resampled time series
        :rtype:   :py:class:`~.TimeSeries`
        """
        t = np.linspace(self.tmin, self.tmax, len(self))
        return self.resampled(t)

    def regular_resample(self):
        """Resample the timeseries to regularly spaced times,
        with the same number of points.

        """
        self._apply_to_self(self.regular_resampled)

    def fixed_frequency_resampled(self, frequency):
        """Return a TimeSeries with same tmin and tmax but resampled at a fixed
        frequency.

        Tmax may vary if the frequency does not lead a integer number of
        timesteps.

        :param frequency: Sampling rate
        :type frequency: float
        :returns:  Time series resampled with given frequency
        :rtype:   :py:class:`~.TimeSeries`
        """
        dt = 1.0 / float(frequency)
        if (dt > self.time_length):
            raise ValueError("Frequency too short for resampling")
        n = int(np.floor(self.time_length / dt))
        # We have to add one to n, so that we can include the tmax point
        new_times = self.tmin + np.arange(0, n + 1) * dt

        return self.resampled(new_times)

    def fixed_frequency_resample(self, frequency):
        """Resample the timeseries to regularly spaced times
        with given frequency.

        Tmax may vary if the frequency does not lead a integer number of
        timesteps.

        :param frequency: Sampling rate
        :type frequency: float
        """
        self._apply_to_self(self.fixed_frequency_resampled, frequency)

    def fixed_timestep_resample(self, timestep):
        """Resample the timeseries to regularly spaced times
        with given timestep.

        Tmax may vary if the timestep does not lead a integer number of
        timesteps.

        :param timestep: New timestep
        :type timestep: float
        :returns:  Time series resampled with given timestep
        :rtype:   :py:class:`~.TimeSeries`

        """
        self._apply_to_self(self.fixed_timestep_resampled, timestep)

    def fixed_timestep_resampled(self, timestep):
        if (timestep > self.time_length):
            raise ValueError("Timestep larger then duration of the TimeSeries")
        frequency = 1.0 / float(timestep)
        return self.fixed_frequency_resampled(frequency)

    def zero_padded(self, N):
        """Return a timeseries that is zero-padded and that has in total
        N points.

        This operation will work only if the timeseries is equispaced.

        :param N: Total number of points of the output timeseries
        :type N: int

        :returns: A new timeseries with in total N points where all
                  the trailing ones are zero
        :rtype: :py:class:`~.TimeSeries`
        """
        N_new_zeros = N - len(self)

        if (N_new_zeros < 0):
            raise ValueError(
                'Zero-padding cannot decrease the number of points')

        new_zeros_t = np.linspace(self.tmax + self.dt,
                                  self.tmax + N_new_zeros * self.dt,
                                  N_new_zeros)
        return TimeSeries(np.append(self.t, new_zeros_t),
                          np.append(self.y, np.zeros(N_new_zeros)))

    def zero_pad(self, N):
        """Pad the timeseries with zeros so that it has a total of N points.

        This operation will work only if the timeseries is equispaced and if N
        is larger than the number of points already present.

        :param N: Total number new points with zeros at the end
        :type N: int

        """
        self._apply_to_self(self.zero_padded, N)

    def mean_removed(self):
        """Return a timeseries with mean removed.

        :returns: A new timeseries zero mean
        :rtype: :py:class:`~.TimeSeries`
        """
        return TimeSeries(self.t, self.y - self.y.mean())

    def mean_remove(self):
        """Remove the mean value from the data."""
        self._apply_to_self(self.mean_removed)

    def time_shifted(self, tshift):
        """Return a new timeseries with time shifted by tshift (what was t = 0
        will be tshift).

        :param tshift: Amount of time to shift
        :type tshift: float

        :returns: A new timeseries with time shifted
        :rtype: :py:class:`~.TimeSeries`
        """
        return TimeSeries(self.t + tshift, self.y)

    def time_shift(self, tshift):
        """Shift the timeseries by tshift (what was t = 0 will be tshift).

        :param N: Amount of time to shift
        :type N: float

        """
        self._apply_to_self(self.time_shifted, tshift)

    def phase_shifted(self, pshift):
        """Return a new timeseries with complex phase shifted by pshift. If the
        signal is real, it is turned complex with phase of pshift.

        :param pshift: Amount of phase to shift
        :type pshift: float

        :returns: A new timeseries with phase shifted
        :rtype: :py:class:`~.TimeSeries`
        """
        return TimeSeries(self.t, self.y * np.exp(1j * pshift))

    def phase_shift(self, pshift):
        """Shift the complex phase timeseries by pshift. If the signal is real,
        it is turned complex with phase of pshift.

        :param pshift: Amount of phase to shift
        :type pshift: float

        """
        self._apply_to_self(self.phase_shifted, pshift)

    def time_unit_changed(self, unit, inverse=False):
        """Return a new timeseries with time scaled by unit.

        When inverse is False, t -> t/unit. For example, if initially the
        units where seconds, with unit=1e-3 the new units will be milliseconds.

        When inverse is True, t -> t * unit. This is useful to convert
        geometrized units to physical units with unitconv.
        For example,

        .. code-block:: python

            # Gravitational waves in geometrized units
            gw_cu = TimeSeries(...)
            # Gravitational waves in seconds, assuming a mass of 1 M_sun
            CU = uc.geom_umass_msun(1)
            gw_s = gw_cu.time_unit_changed(CU.time, inverse=True)

        :param unit: New time unit
        :type unit: float
        :param inverse: If True, time = 1 -> time = unit, otherwise
                        time = unit -> 1
        :type inverse: bool

        :returns: A timeseries with new time unit
        :rtype: :py:class:`~.TimeSeries`

        """
        factor = unit if inverse else 1/unit
        return TimeSeries(self.t * factor, self.y)

    def time_unit_change(self, unit, inverse=False):
        """Rescale time units by unit.

        When inverse is False, t -> t/unit. For example, if initially the
        units where seconds, with unit=1e-3 the new units will be milliseconds.

        When inverse is True, t -> t * unit. This is useful to convert
        geometrized units to physical units with unitconv.
        For example,

        .. code-block:: python

            # Gravitational waves in geometrized units
            gw_cu = TimeSeries(...)
            # Gravitational waves in seconds, assuming a mass of 1 M_sun
            CU = uc.geom_umass_msun(1)
            gw_cu.time_unit_change(CU.time, inverse=True)

        :param unit: New time unit
        :type unit: float
        :param inverse: If True, time = 1 -> time = unit, otherwise
                        time = unit -> 1
        :type inverse: bool

        """
        self._apply_to_self(self.time_unit_changed, unit, inverse)

    def redshifted(self, z):
        """Return a new timeseries with time rescaled so that frequencies are
        redshited by 1 + z.

        :param z: Redshift factor
        :type z: float

        :returns: A new redshifted timeseries
        :rtype: :py:class:`~.TimeSeries`

        """
        return self.time_unit_changed(1 + z, inverse=True)

    def redshift(self, z):
        """Apply redshift to the data by rescaling the time.

        :param z: Redshift factor

        """
        self._apply_to_self(self.redshifted, z)

    def unfolded_phase(self):
        """Compute the complex phase of a complex-valued signal such that
        no phase wrap-arounds occur, i.e. if the input is continous, so is
        the output.

        :returns:   Continuous complex phase
        :rtype:     :py:class:`~.TimeSeries`
        """

        return TimeSeries(self.t, unfold_phase(np.angle(self.y)))

    def phase_angular_velocity(self, use_splines=True, tsmooth=None, order=3):
        """Compute the phase angular velocity, i.e. the time derivative of the
        complex phase.

        Optionally smooth the with a savgol filter with smoothing length
        tsmooth and order order. If you do so, the timeseries is resampled to
        regular timesteps.

        :param use_splines: Wheter to use splines of finite differencing for
                            the derivative
        :type use_splines: bool
        :param tsmooth: Time over which smoothing is applied
        :type tsmooth: float
        :param order: Order of the for the savgol smoothing
        :type order: int

        :returns:  Time derivative of the complex phase
        :rtype:    :py:class:`~.TimeSeries`
        """
        if use_splines:
            ret_value = self.unfolded_phase().spline_derived()
        else:
            ret_value = self.unfolded_phase().derived()

        if tsmooth is not None:
            ret_value.savgol_smooth_time(tsmooth, order)

        return ret_value

    def phase_frequency(self, use_splines=True, tsmooth=None, order=3):
        """Compute the phase frequency, i.e. the time derivative
        of the complex phase divided by 2 pi.

        Optionally smooth the with a savgol filter with smoothing length
        tsmooth and order order. If you do so, the timeseries is resampled
        to regular timesteps.

        :param use_splines: Wheter to use splines of finite differencing for
                            the derivative
        :type use_splines: bool
        :param tsmooth: Time over which smoothing is applied
        :type tsmooth: float
        :param order: Order of the for the savgol smoothing
        :type order: int

        :returns:  Time derivative of the complex phase divided by 2 pi
        :rtype:    :py:class:`~.TimeSeries`
        """
        return self.phase_angular_velocity(use_splines,
                                           tsmooth, order) / (2 * np.pi)

    def windowed(self, window_function, *args, **kwargs):
        """Return a timeseries windowed with window_function.

        ``window_function`` has to be a function that takes as first argument
        the number of points of the signal. window_function can take additional
        arguments as passed by windowed.

        :param window: Window function to apply to the timeseries
        :type window: callable

        :returns:  New windowed timeseries
        :rtype:    :py:class:`~.TimeSeries`

        """
        window_array = window_function(len(self), *args, **kwargs)
        return TimeSeries(self.t, self.y * window_array)

    def window(self, window_function, *args, **kwargs):
        """Apply window_function to the data.

        ``window_function`` has to be a function that takes as first argument
        the number of points of the signal. window_function can take additional
        arguments as passed by windowed.

        :param window: Window function to apply to the timeseries
        :type window: callable

        """
        self._apply_to_self(self.windowed, window_function,
                            *args, **kwargs)

    def tukey_windowed(self, alpha):
        """Return a timeseries with Tukey window with paramter alpha applied.

        :param alpha: Tukey parameter
        :type alpha: float

        :returns:  New windowed timeseries
        :rtype:    :py:class:`~.TimeSeries`

        """
        return self.windowed(signal.tukey, alpha)

    def tukey_window(self, alpha):
        """Apply Tukey window.

        :param alpha: Tukey parameter
        :type alpha: float

        """
        self.window(signal.tukey, alpha)

    def hamming_windowed(self):
        """Return a timeseries with Hamming window applied.

        :returns:  New windowed timeseries
        :rtype:    :py:class:`~.TimeSeries`

        """
        return self.windowed(signal.hamming)

    def hamming_window(self):
        """Apply Hamming window.

        """
        self.window(signal.hamming)

    def blackman_windowed(self):
        """Return a timeseries with Blackman window applied.

        """
        return self.windowed(signal.blackman)

    def blackman_window(self):
        """Apply Blackman window.

        """
        self.window(signal.blackman)

    def savgol_smoothed_time(self, tsmooth, order=3):
        """Return a resampled timeseries with uniform timesteps, smoothed it
        with savgol_smooth with a window that is tsmooth in time (as opposed
        to a number of points).

        :param tsmooth: Time interval over which to smooth
        :type tsmooth: float
        :param order: Order of the filter
        :type order: int

        :returns:  New smoothed and resampled timeseries
        :rtype:    :py:class:`~.TimeSeries`

        """
        ts = self.regular_resampled()
        dt = ts.t[1] - ts.t[0]
        # The savgol method requires a odd window
        # If it is not, we add one point
        window = int(np.rint(tsmooth / dt))
        window = window + 1 if (window % 2 == 0) else window
        return self.savgol_smoothed(window, order)

    def savgol_smooth_time(self, tsmooth, order=3):
        """Resampl the timeseries with uniform timesteps, smooth it with
        savgol_smooth with a window that is tsmooth in time (as opposed to a
        number of points).

        :param tsmooth: Time interval over which to smooth
        :type tsmooth: float
        :param order: Order of the filter
        :type order: int

        """
        self._apply_to_self(self.savgol_smoothed_time, tsmooth, order)

    def to_FrequencySeries(self):
        """Return a FrequencySeries that is the Fourier transform of
        the timeseries.

        If the signal is not complex, only positive frequencies are kept.

        The timeseries is regularly sampled before transforming.

        :: warning:

            To have meaningful results, you should consider removing the
            mean and windowing the signal before calling this method!

        :returns: Fourier Transform
        :rtype: :py:class:`~.FrequencySeries`

        """
        regular_ts = self.regular_resampled()
        dt = regular_ts.dt
        freqencies = np.fft.fftfreq(len(regular_ts), d=dt)
        fft = np.fft.fft(regular_ts.y)

        f = np.fft.fftshift(freqencies)
        fft = np.fft.fftshift(fft)

        return frequencyseries.FrequencySeries(f, fft)