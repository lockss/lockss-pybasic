==============
lockss-pybasic
==============

.. |RELEASE| replace:: 0.3.0-dev5
.. |RELEASE_DATE| replace:: NOT YET RELEASED

**Latest release:** |RELEASE| (|RELEASE_DATE|)

``lockss-pybasic`` provides basic utilities for various LOCKSS projects written in Python.

-------
Modules
-------

``lockss.pybasic.cliutil``
   Command line utilities based on `Click Extra <https://kdeldycke.github.io/click-extra>`_, `Cloup <https://cloup.readthedocs.io/>`_ and `Click <https://click.palletsprojects.com/>`_.

   *  ``click_path()``: a ``click.Path`` utility.

   *  ``PositiveInt``, ``NonNegativeInt``, ``NegativeInt``, ``NonPositiveInt``, ``UInt16``: ``click.ParamType`` integer types.

   *  ``compose_decorators()``: a decorator utility.

   *  ``make_table_format_option()``: a remix of ``click_extra.table_format_option`` that is not attached to the top-level command.

   *  ``make_extra_context_settings()``: a custom ``click_extra.ExtraContext``.

``lockss.pybasic.errorutil``
   Error and exception utilities.

   *  ``InternalError`` is a no-arg subclass of ``RuntimeError``.

``lockss.pybasic.fileutil``
   File and path utilities.

   *  ``file_lines`` returns the non-empty lines of a file stripped of comments that begin with ``#`` and run to the end of a line.

   *  ``path`` takes a string or ``PurePath`` and returns a ``Path`` for which ``Path.expanduser()`` and ``Path.resolve()`` have been called.

-------------
Release Notes
-------------

See `<CHANGELOG.rst>`_.
