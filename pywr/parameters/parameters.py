import os
import datetime
from ..parameter_property import parameter_property
from ._parameters import (
    Parameter, parameter_registry, UnutilisedDataWarning, ConstantParameter,
    ConstantScenarioParameter, ConstantScenarioIndexParameter, AnnualHarmonicSeriesParameter,
    ArrayIndexedParameter, ConstantScenarioParameter, IndexedArrayParameter,
    ArrayIndexedScenarioMonthlyFactorsParameter, TablesArrayParameter,
    DailyProfileParameter, MonthlyProfileParameter, WeeklyProfileParameter,
    ArrayIndexedScenarioParameter, ScenarioMonthlyProfileParameter,
    align_and_resample_dataframe, DataFrameParameter,
    IndexParameter, AggregatedParameter, AggregatedIndexParameter, PiecewiseIntegralParameter,
    NegativeParameter, MaxParameter, NegativeMaxParameter, MinParameter, NegativeMinParameter,
    DeficitParameter, load_parameter, load_parameter_values, load_dataframe)
from . import licenses
from ._polynomial import Polynomial1DParameter, Polynomial2DStorageParameter
from ._thresholds import StorageThresholdParameter, RecorderThresholdParameter
from ._hydropower import HydropowerTargetParameter
from past.builtins import basestring
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import quad
import pandas


class FunctionParameter(Parameter):
    def __init__(self, model, parent, func, *args, **kwargs):
        super(FunctionParameter, self).__init__(model, *args, **kwargs)
        self._parent = parent
        self._func = func

    def value(self, ts, scenario_index):
        return self._func(self._parent, ts, scenario_index)
FunctionParameter.register()


class ScaledProfileParameter(Parameter):
    def __init__(self, model, scale, profile, *args, **kwargs):
        super(ScaledProfileParameter, self).__init__(model, *args, **kwargs)
        self.scale = scale

        profile.parents.add(self)
        self.profile = profile

    @classmethod
    def load(cls, model, data):
        scale = float(data.pop("scale"))
        profile = load_parameter(model, data.pop("profile"))
        return cls(model, scale, profile, **data)

    def value(self, ts, si):
        p = self.profile.get_value(si)
        return self.scale * p
ScaledProfileParameter.register()


class AbstractInterpolatedParameter(Parameter):
    def __init__(self, model, x, y, interp_kwargs=None, **kwargs):
        super(AbstractInterpolatedParameter, self).__init__(model, **kwargs)
        self.x = x
        self.y = y
        self.interp = None
        default_interp_kwargs = dict(kind='linear', bounds_error=True)
        if interp_kwargs is not None:
            # Overwrite or add to defaults with given values
            default_interp_kwargs.update(interp_kwargs)
        self.interp_kwargs = default_interp_kwargs

    def _value_to_interpolate(self, ts, scenario_index):
        raise NotImplementedError()

    def setup(self):
        super(AbstractInterpolatedParameter, self).setup()
        self.interp = interp1d(self.x, self.y, **self.interp_kwargs)

    def value(self, ts, scenario_index):
        v = self._value_to_interpolate(ts, scenario_index)
        return self.interp(v)


class InterpolatedParameter(AbstractInterpolatedParameter):
    """
    Parameter value is equal to the interpolation of another parameter

    Example
    -------
    >>> x = [0, 5, 10, 20]
    >>> y = [0, 10, 30, -5]
    >>> p1 = ConstantParameter(model, 9.3) # or something more interesting
    >>> p2 = InterpolatedParameter(model, p1, x, y, interp_kwargs={"kind": "linear"})
    """
    def __init__(self, model, parameter, x, y, interp_kwargs=None, **kwargs):
        super(InterpolatedParameter, self).__init__(model, x, y, interp_kwargs, **kwargs)
        self._parameter = None
        self.parameter = parameter

    parameter = parameter_property("_parameter")

    def _value_to_interpolate(self, ts, scenario_index):
        return self._parameter.get_value(scenario_index)

    @classmethod
    def load(cls, model, data):
        parameter = load_parameter(model, data.pop("parameter"))
        x = np.array(data.pop("x"))
        y = np.array(data.pop("y"))
        kind = data.pop("kind", "linear")
        return cls(model, parameter, x, y, interp_kwargs={'kind': kind})
InterpolatedParameter.register()


class InterpolatedVolumeParameter(AbstractInterpolatedParameter):
    """
    Generic interpolation parameter calculated from current volume
    """
    def __init__(self, model, node, x, y, interp_kwargs=None, **kwargs):
        super(InterpolatedVolumeParameter, self).__init__(model, x, y, interp_kwargs, **kwargs)
        self._node = node

    def _value_to_interpolate(self, ts, scenario_index):
        return self._node.volume[scenario_index.global_id]

    @classmethod
    def load(cls, model, data):
        node = model._get_node_from_ref(model, data.pop("node"))
        volumes = np.array(data.pop("volumes"))
        values = np.array(data.pop("values"))
        kind = data.pop("kind", "linear")
        return cls(model, node, volumes, values, interp_kwargs={'kind': kind})
InterpolatedVolumeParameter.register()


class InterpolatedFlowParameter(AbstractInterpolatedParameter):
    """
    Generic interpolation parameter that uses a node's  flow at the previous time-step for interpolation.

    """
    def __init__(self, model, node, x, y, interp_kwargs=None, **kwargs):
        super().__init__(model, x, y, interp_kwargs, **kwargs)
        self._node = node

    def _value_to_interpolate(self, ts, scenario_index):       
        return self._node.prev_flow[scenario_index.global_id]

    @classmethod
    def load(cls, model, data):
        node = model._get_node_from_ref(model, data.pop("node"))
        volumes = np.array(data.pop("flows"))
        values = np.array(data.pop("values"))
        kind = data.pop("kind", "linear")
        return cls(model, node, volumes, values, interp_kwargs={'kind': kind})
InterpolatedFlowParameter.register()


class InterpolatedQuadratureParameter(AbstractInterpolatedParameter):
    """Parameter value is equal to the quadrature of the interpolation of another parameter

    Parameters
    ----------
    upper_parameter : Parameter
        Upper value of the interpolated interval to integrate over.
    x : array_like
        x coordinates of the data points for interpolation.
    y : array_like
        y coordinates of the data points for interpolation.
    lower_parameter : Parameter or None
        Lower value of the interpolated interval to integrate over. Can be `None` in which
        case the lower value of interval is zero.
    interp_kwargs : dict
        Dictionary of keyword arguments to pass to `scipy.interpolate.interp1d` class and used
        for interpolation.

    Example
    -------
    >>> x = [0, 5, 10, 20]
    >>> y = [0, 10, 30, -5]
    >>> p1 = ConstantParameter(model, 9.3) # or something more interesting
    >>> p2 = InterpolatedQuadratureParameter(model, p1, x, y, interp_kwargs={"kind": "linear"})
    """
    def __init__(self, model, upper_parameter, x, y, lower_parameter=None, interp_kwargs=None, **kwargs):
        super().__init__(model, x, y, interp_kwargs, **kwargs)
        self._upper_parameter = None
        self.upper_parameter = upper_parameter
        self._lower_parameter = None
        self.lower_parameter = lower_parameter

    upper_parameter = parameter_property("_upper_parameter")
    lower_parameter = parameter_property("_lower_parameter")

    def _value_to_interpolate(self, ts, scenario_index):
        return self._upper_parameter.get_value(scenario_index)

    def value(self, ts, scenario_index):
        a = 0
        if self._lower_parameter is not None:
            a = self._lower_parameter.get_value(scenario_index)
        b = self._value_to_interpolate(ts, scenario_index)

        cost, err = quad(self.interp, a, b)
        return cost

    @classmethod
    def load(cls, model, data):
        upper_parameter = load_parameter(model, data.pop("upper_parameter"))
        lower_parameter = load_parameter(model, data.pop("lower_parameter", None))
        x = np.array(data.pop("x"))
        y = np.array(data.pop("y"))
        kind = data.pop("kind", "linear")
        return cls(model, upper_parameter, x, y, lower_parameter=lower_parameter,
                   interp_kwargs={'kind': kind})
InterpolatedQuadratureParameter.register()


class ScenarioWrapperParameter(Parameter):
    """Parameter that utilises a different child parameter in each scenario ensemble.

    This parameter is used to switch between different child parameters based on different
    ensembles in a given `Scenario`. It can be used to vary data in a non-scenario aware
    parameter type across multiple scenario ensembles. For example, many of control curve or
    interpolation parameters do not explicitly support scenarios. This parameter can be used
    to test multiple control curve definitions as part of a single simulation.

    Parameters
    ----------
    scenario : Scenario
        The scenario instance which is used to select the parameters.
    parameters : iterable of Parameter instances
        The child parameters that are used in each of `scenario`'s ensembles. The number
        of parameters must equal the size of the given scenario.

    """
    def __init__(self, model, scenario, parameters, **kwargs):
        super().__init__(model, **kwargs)
        if scenario.size != len(parameters):
            raise ValueError("The number of parameters must equal the size of the scenario.")
        self.scenario = scenario
        self.parameters = []
        for p in parameters:
            self.children.add(p)
            self.parameters.append(p)
        # Initialise internal attributes
        self._scenario_index = None

    def setup(self):
        super().setup()
        # This setup must find out the index of self._scenario in the model
        # so that it can return the correct value in value()
        self._scenario_index = self.model.scenarios.get_scenario_index(self.scenario)

    def value(self, ts, scenario_index):
        # This is a bit confusing.
        # scenario_indices contains the current scenario number for all
        # the Scenario objects in the model run. We have cached the
        # position of self._scenario in self._scenario_index to lookup the
        # correct number to use in this instance.
        parameter = self.parameters[scenario_index.indices[self._scenario_index]]
        return parameter.get_value(scenario_index)

    @classmethod
    def load(cls, model, data):
        scenario = model.scenarios[data.pop('scenario')]

        parameters = [load_parameter(model, p) for p in data.pop('parameters')]
        return cls(model, scenario, parameters, **data)
ScenarioWrapperParameter.register()


def pop_kwarg_parameter(kwargs, key, default):
    """Pop a parameter from the keyword arguments dictionary

    Parameters
    ----------
    kwargs : dict
        A keyword arguments dictionary
    key : string
        The argument name, e.g. 'flow'
    default : object
        The default value to use if the dictionary does not have that key

    Returns a Parameter
    """
    value = kwargs.pop(key, default)
    if isinstance(value, Parameter):
        return value
    elif callable(value):
        # TODO this is broken?
        return FunctionParameter(self, value)
    else:
        return value


class PropertiesDict(dict):
    def __setitem__(self, key, value):
        if not isinstance(value, Property):
            value = ConstantParameter(value)
        dict.__setitem__(self, key, value)

