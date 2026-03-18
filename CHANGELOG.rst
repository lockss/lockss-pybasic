=============
Release Notes
=============

-----
0.2.0
-----

Released: NOT YET RELEASED

Requires Python 3.10.

*  **Features**

   *  ``lockss.pybasic.cliutil`` has been replaced with utilities based on `Click Extra <https://kdeldycke.github.io/click-extra>`_, `Cloup <https://cloup.readthedocs.io/>`_ and `Click <https://click.palletsprojects.com/>`_:

      *  ``click_path()``: a ``click.Path`` utility.

      *  ``PositiveInt``, ``NonNegativeInt``, ``NegativeInt``, ``NonPositiveInt``, ``UInt16``: ``click.ParamType`` integer types.

      *  ``compose_decorators()``: a decorator utility.

      *  ``make_table_format_option()``: a remix of Click Extra's ``table_Format_option`` that is not attached to the top-level command.

      *  ``make_extra_context_settings()``: a standard ``click_extra.commands.ExtraContext``.

      ``lockss.pybasic.outpututil`` has been removed.

-----
0.1.1
-----

Released: 2025-10-02

*  **Bug Fixes**

   *  Remove Python 3.12+ f-string quote reuse (lockss-pybasic is Python 3.9+).

-----
0.1.0
-----

Released: 2025-07-01

Initial release, including:

*  ``cliutil``

*  ``errorutil``

*  ``fileutil``

*  ``outpututil``
