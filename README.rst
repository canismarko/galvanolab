Galvanolab
==========

.. image:: https://travis-ci.org/canismarko/galvanolab.svg?branch=master
    :target: https://travis-ci.org/canismarko/galvanolab

Galvanolab is a set of tools for interacting with electrochemical
data. Currently it only supports galvanostatic cycling using the
BioLogic software suite. Files should be exported as ``.mpt`` files
and can then be imported using::

  from galvanolab import GalvanostatRun
  gv = GalvanostatRun(filename="eclabdata.mpt")
  gv.plot_cycles()

There is also a ``CyclicVoltammogram`` class to works similarly.

Galvanolab makes use of the Pint_ library to ensure that quantities
are consistent and has a units registry built in. Any function or
method that accepts a quantitiy (eg. mass), should be given a
unit-aware value::

  ureg = galvanolab.electrochem_units.ureg
  mg = ureg.milligram
  gv = GalvanostatRun(filename="eclabdata.mpt", mass=22.54*mg)

.. _Pint: https://pypi.org/project/Pint/
