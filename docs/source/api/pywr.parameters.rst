Parameters
==========

.. currentmodule:: pywr.parameters


Base Parameter class
--------------------

All the `Parameter` subclasses in `pywr` are descended from a common base class.

.. autosummary::
   :toctree: generated/

   Parameter
   IndexParameter


Simple parameters
-----------------

.. autosummary::
   :toctree: generated/

   ConstantParameter
   ConstantScenarioParameter
   ConstantScenarioIndexParameter


Combining multiple parameters
-----------------------------

.. autosummary::
   :toctree: generated/

   AggregatedParameter
   AggregatedIndexParameter
   DivisionParameter
   NegativeParameter
   MaxParameter
   NegativeMaxParameter
   MinParameter
   NegativeMinParameter

Annual profile parameters
-------------------------

.. autosummary::
   :toctree: generated/

   DailyProfileParameter
   WeeklyProfileParameter
   MonthlyProfileParameter
   ScenarioMonthlyProfileParameter
   ArrayIndexedScenarioMonthlyFactorsParameter

Dataframe parameter
-------------------

.. autosummary::
   :toctree: generated/

   DataFrameParameter


HDF5 Parameter
--------------
.. autosummary::
   :toctree: generated/

   TablesArrayParameter


Array based parameters
----------------------

.. autosummary::
   :toctree: generated/

   ArrayIndexedParameter
   ArrayIndexedScenarioParameter
   IndexedArrayParameter


Interpolation parameters
------------------------

.. autosummary::
   :toctree: generated/

    InterpolatedParameter
    InterpolatedVolumeParameter
    InterpolatedQuadratureParameter


Control curve parameters
------------------------

.. autosummary::
    :toctree: generated/

    control_curves.BaseControlCurveParameter
    control_curves.ControlCurveInterpolatedParameter
    control_curves.ControlCurveIndexParameter

Hydropower parameters
----------------------

.. autosummary::
   :toctree: generated/

   HydropowerTargetParameter


Other parameters
----------------

.. autosummary::
   :toctree: generated/

   AnnualHarmonicSeriesParameter
   DeficitParameter
   ScenarioWrapperParameter
   PiecewiseIntegralParameter


