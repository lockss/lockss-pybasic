==============
lockss-pybasic
==============

.. |RELEASE| replace:: 0.1.0
.. |RELEASE_DATE| replace:: 2025-07-01

**Latest release:** |RELEASE| (|RELEASE_DATE|)

``lockss-pybasic`` provides basic utilities for various LOCKSS projects written in Python.

-------
Modules
-------

``lockss.pybasic.cliutil``
   Command line utilities.

   *  ``BaseCli`` is a base class for command line interfaces that uses `pydantic-argparse <https://pypi.org/project/pydantic-argparse/>`_ to define arguments and subcommands, and `rich-argparse <https://pypi.org/project/rich-argparse/>`_ to display help messages. For each command ``x-y-z`` induced by a ``pydantic-argparse`` field named ``x_y_z`` deriving from ``BaseModel`` , the ``dispatch()`` method expects a method named ``_x_y_z``.

   *  ``StringCommand`` provides a `pydantic-argparse <https://pypi.org/project/pydantic-argparse/>`_ way to define a subcommand whose only purpose is printing a string, with ``COPYRIGHT_DESCRIPTION``, ``LICENSE_DESCRIPTION`` and ``VERSION_DESCRIPTION`` constants provided for convenience. Example:

      .. code-block:: python

         class MyCliModel(BaseModel):
             copyright: Optional[StringCommand.type(my_copyright_string)] = Field(description=COPYRIGHT_DESCRIPTION)

   *  ``at_most_one_from_enum`` and ``get_from_enum`` provide a facility for defining a `pydantic-argparse <https://pypi.org/project/pydantic-argparse/>`_ model that defines one command line option per constant of an ``Enum``, using an ``enum`` keyword argument in the ``Field`` definition. Example:

      .. code-block:: python

         class Orientation(Enum):
             horizontal = 1
             vertical = 2
             diagonal = 3

         DEFAULT_ORIENTATION = Orientation.horizontal

         class MyCliModel(BaseModel):
             diagonal: Optional[bool] = Field(False, description='display diagonally', enum=Orientation)
             horizontal: Optional[bool] = Field(False, description='display horizontally', enum=Orientation)
             unrelated: Optional[bool] = Field(...)
             vertical: Optional[bool] = Field(False, description='display vertically', enum=Orientation)

             @root_validator
             def _at_most_one_orientation(cls, values):
                 return at_most_one_from_enum(cls, values, Orientation)

             def get_orientation(self) -> Orientation:
                 return get_from_enum(self, Orientation, DEFAULT_ORIENTATION)

``lockss.pybasic.errorutil``
   Error and exception utilities.

   *  ``InternalError`` is a no-arg subclass of ``RuntimeError``.

``lockss.pybasic.fileutil``
   File and path utilities.

   *  ``file_lines`` returns the non-empty lines of a file stripped of comments that begin with ``#`` and run to the end of a line.

   *  ``path`` takes a string or ``PurePath`` and returns a ``Path`` for which ``Path.expanduser()`` and ``Path.resolve()`` have been called.

``lockss.pybasic.outpututil``
   Utilities to work with `tabulate <https://pypi.org/project/tabulate/>`_.

   *  ``OutputFormat`` is an ``Enum`` of all the output formats from ``tabulate.tabulate_formats``.

   *  ``OutputFormatOptions`` defines a `pydantic-argparse <https://pypi.org/project/pydantic-argparse/>`_ model for setting an output format from ``OutputFormat``.

-------------
Release Notes
-------------

See `<CHANGELOG.rst>`_.