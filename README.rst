Galvanolab
==========

Galvanolab is a set of tools for interacting with electrochemical
data. Currently it only supports galvanostatic cycling using the
BioLogic software suite. Files should be exported as ``.mpt`` files
and can then be imported using::

  from galvanolab import GalvanostatRun
  gv = GalvanostatRun(filename="eclabdata.mpt")
  gv.plot_cycles()

Galvanolab makes use of the ``units`` library to ensure that
quantities are consistent. Any function or method that accepts a
quantitiy (eg. mass), should be given a unit-aware value::

  mg = units.unit('mg')
  gv = GalvanostatRun(filename="eclabdata.mpt", mass=mg(22.54))


