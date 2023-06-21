from __future__ import annotations

import numpy as np
import xarray as xr


def _concat_hist(da, **hist):
    """Concatenate historical scenario with future scenarios along time.

    Parameters
    ----------
    da : xr.DataArray
      Input data where the historical scenario is stored alongside other, future, scenarios.
    hist: {str: str}
      Mapping of the scenario dimension name to the historical scenario coordinate, e.g. `scen="historical"`.

    Returns
    -------
    xr.DataArray
      Data with the historical scenario is stacked in time before each one of the other scenarios.

    Notes
    -----
    Data goes from:

        +----------+----------------------------------+
        | Scenario | Time                             +
        +==========+==================================+
        | hist     | hhhhhhhhhhhhhhhh                 |
        +----------+----------------------------------+
        | scen1    |                 111111111111     |
        +----------+----------------------------------+
        | scen2    |                 222222222222     |
        +----------+----------------------------------+

    to:
        +----------+----------------------------------+
        | Scenario | Time                             +
        +==========+==================================+
        | scen1    | hhhhhhhhhhhhhhhh111111111111     |
        +----------+----------------------------------+
        | scen2    | hhhhhhhhhhhhhhhh222222222222     |
        +----------+----------------------------------+
    """
    if len(hist) > 1:
        raise ValueError("Too many values in hist scenario.")

    # Scenario dimension, and name of the historical scenario
    ((dim, name),) = hist.items()

    # Select historical scenario and drop it from the data
    h = da.sel(**hist).dropna("time", how="all")
    ens = da.drop_sel(**hist)

    index = ens[dim]
    bare = ens.drop(dim).dropna("time", how="all")

    return xr.concat([h, bare], dim="time").assign_coords({dim: index})


def _model_in_all_scens(da, dimensions=None):
    """Return data with only simulations that have at least one member in each scenario.

    Parameters
    ----------
    da: xr.DataArray
      Input data with dimensions for time, member, model and scenario.
    dimensions: dict
      Mapping from original dimension names to standard dimension names: scenario, model, member.

    Returns
    -------
    xr.DataArray
      Data for models that have values for all scenarios.

    Notes
    -----
    In the following example, `GCM_C` would be filtered out from the data because it has no member for `scen2`.

    +-------+-------+-------+
    | Model | Members       |
    +-------+---------------+
    |       | scen1 | scen2 |
    +=======+=======+=======+
    | GCM_A | 1,2,3 | 1,2,3 |
    +-------+-------+-------+
    | GCM_B | 1     | 2,3   |
    +-------+-------+-------+
    | GCM_C | 1,2,3 |       |
    +-------+-------+-------+
    """
    if dimensions is None:
        dimensions = {}

    da = da.rename(reverse_dict(dimensions))

    ok = da.notnull().any("time").any("member").all("scenario")

    return da.sel(model=ok).rename(dimensions)


def _single_member(da, dimensions=None):
    """Return data for a single member per model.

    Parameters
    ----------
    da : xr.DataArray
      Input data with dimensions for time, member, model and scenario.
    dimensions: dict
      Mapping from original dimension names to standard dimension names: scenario, model, member.

    Returns
    -------
    xr.DataArray
      Data with only one member per model.

    Notes
    -----
    In the following example, the original members would be filtered to return only the first member found for each
    scenario.

    +-------+-------+-------+----+-------+-------+
    | Model | Members       |    | Selected      |
    +-------+---------------+----+---------------+
    |       | scen1 | scen2 |    | scen1 | scen2 |
    +=======+=======+=======+====+=======+=======+
    | GCM_A | 1,2,3 | 1,2,3 |    | 1     | 1     |
    +-------+-------+-------+----+-------+-------+
    | GCM_B | 1,2   | 2,3   |    | 1     | 2     |
    +-------+-------+-------+----+-------+-------+
    """
    if dimensions is None:
        dimensions = {}

    da = da.rename(reverse_dict(dimensions))

    # Stack by simulation specifications - drop simulations with missing values
    full = da.stack(i=("scenario", "model", "member")).dropna("i", how="any")

    # Pick first run with data
    s = full.i.to_series()
    s[:] = np.arange(len(s))
    i = s.unstack().T.min().to_list()

    out = full.isel(i=i).unstack().squeeze()
    return out.rename(dimensions)


def reverse_dict(d):
    """Reverse dictionary."""
    return {v: k for (k, v) in d.items()}
