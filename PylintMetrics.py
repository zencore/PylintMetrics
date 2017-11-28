# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""

    PylintMetrics.py

A little script that calculates some pylint metrics.

basic usage:

    python PylintMetrics.py [module names]

metric output to file:

    python PylintMetrics.py [module names] -f <filename>

pylint output to file:

    python PylintMetrics.py [module names] -o <filename>

custom pylint config file:

    python PylintMetrics.py [module names] -c <filename>


Author: Marc Gouw, 2017
Licence: GNU GPL 3.0
"""

from __future__ import print_function
import re
import argparse
from pylint import epylint as lint


class PylintMetrics(object):
    """ Parse and print pylint metrics.

    Options for pylint can only be passed by supplying a path to a pylint
    configuration file.
    """

    def __init__(self, modules, conf=None):
        """ PylintMetrics object, parse pylint code

        Args:
            modules (str): modules analyse (separated by spaces)
            conf (str):    path of the pylint configuration file.
        """

        if conf is None:
            self.cmd = "{0} --reports=y".format(modules)
        else:
            self.cmd = "{0} --reports=y --rcfile={1}".format(
                modules, conf
            )
        print(self.cmd)

        # store pyline output
        self._stdout = None
        self._stderr = None
        self._stdout_l = None
        self._stderr_l = None

        # where to store metrics
        self._raw_metrics = None
        self._duplication = None
        self._messages = None
        self._score = None

        # regular expression to parse ascii table rows (first 2 columns only)
        self._row_parser = re.compile(
            r"^\s\|(?P<metric>.*?)\s+\|(?P<value>.*?)\s+\|.*$"
        )

        # No configuration file "error"
        self._no_config_msg = (
            "No config file found, using default configuration"
        )

        # Pyline score message:
        self._score_message = re.compile(
            r" Your code has been rated at (?P<score>[-]?\d+(?:\.\d+))\/10.*"
        )

    def run(self):
        """ Just run everything.
        """
        self._run()
        self._check()
        self._parse()

    def _get_parsed_block(self, first_row, num_rows):
        """ Parse the ascii table in self._stdout_l, and return a dictionary of
        metrics + values.

        Args:
            first_row (int): Index of the first row of the table (content line)
            num_rows (int) : Number of rows to read from the table
        """

        data = {}

        lines = range(first_row, first_row + 2 * num_rows, 2)

        for i in lines:

            match = self._row_parser.search(self._stdout_l[i])

            if not match:
                raise Exception("Something went wrong parsing")

            gdict = match.groupdict()

            metric = gdict['metric'].replace(' ', '_')
            value = int(float(gdict['value']))

            data[metric] = value

        return data

    def _get_parse_score(self):
        """ Parse outout for the final score, and return the value.

        Returns:
            score (float): pylint code score.
        """

        self._check()

        line = self._stdout_l[-3]

        match = self._score_message.match(line)

        if not match:
            raise Exception("Could not parse score from pylint.")

        return float(match.groupdict()['score'])

    def _parse(self):
        """ Parse output for three metric tables, and store values.
        """

        ind = self._stdout_l.index(" Raw metrics")  # leading space required
        data = self._get_parsed_block(ind+6, 4)
        self._raw_metrics = data

        ind = self._stdout_l.index(" Duplication")  # leading space required
        data = self._get_parsed_block(ind+6, 2)
        self._duplication = data

        ind = self._stdout_l.index(
            " Messages by category"  # leading space required
        )
        data = self._get_parsed_block(ind+6, 4)
        self._messages = data

        self._score = self._get_parse_score()

    def _check(self):
        """ Make sure it looks like pylint ran corrently. Raise an exception if
        it probably did not."""

        if self._stdout is None:
            raise Exception(
                "No stdout captured. Did we run pylint?"
            )
        if (self._stderr) and (self._stderr != self._stderr):
            raise Exception(
                "pylint run caused errors:\n\n{0}".format(self._stderr)
            )
        if not (self._stdout) and (self._stderr != self._stderr):
            raise Exception(
                "No stdout captured. Did we run pylint?"
            )

    def _run(self):
        """ Run pylint, and save output.
        """

        (stdout, stderr) = lint.py_run(self.cmd, return_std=True)
        self._stdout = stdout.read()
        self._stdout_l = self._stdout.split("\n")
        self._stderr = stderr.read()
        self._stderr_l = self._stderr.split("\n")

    def print_metrics(self):
        """ Print metrics to screen

        Args:
            fname (str): filename to print to

        """

        self._check()

        data = {}
        data.update(self._raw_metrics)
        data.update(self._duplication)
        data.update(self._messages)
        data.update({'score': self._score})

        for key, value in data.items():

            print("{0}: {1}".format(key, value))

    def write_metrics(self, fname):
        """  Print the metrics to a file.

        Args:
            fname (str): filename to print to

        """

        self._check()

        data = {}
        data.update(self._raw_metrics)
        data.update(self._duplication)
        data.update(self._messages)
        data.update({'score': self._score})

        out = open(fname, 'w')

        for key, value in data.items():

            out.write("{0}\t {1}\n".format(key, value))

        out.close()

    def write_output(self, fname):
        """  Print the pylint output to a file.

        The "reports" section is not included.

        Args:
            fname (str): filename to print to

        """

        self._check()

        out = open(fname, 'w')

        for line in self._stdout_l:

            if line == " Report":
                break
            out.write("{0}\n".format(line))

        out.close()


def build_parser():
    """ Build and return the PylintMetrics argparser.
    """

    parser = argparse.ArgumentParser(
        description="Pylint Metrics Parser."
    )

    # modules argument
    parser.add_argument(
        "modules",
        nargs="+",
        help="modules to analyze",
    )

    # conf argument
    parser.add_argument(
        "-c",
        "--conf",
        help="pylint confiruration file",
        required=False,
    )

    # outfile argument
    parser.add_argument(
        "-o",
        "--outfile",
        help="output file",
        required=False,
    )

    # outfile argument
    parser.add_argument(
        "-f",
        "--file",
        help="Metrics output file",
        required=False,
    )

    return parser


if __name__ == "__main__":

    parser = build_parser()

    args = parser.parse_args()

    pm = PylintMetrics(
        " ".join(args.modules), conf=args.conf,
    )

    pm.run()

    if args.file is not None:
        pm.write_metrics(args.file)
        print("Wrote metrics to: {0}".format(args.file))
    else:
        pm.print_metrics()

    if args.outfile is not None:
        pm.write_output(args.outfile)
        print("Wrote output to: {0}".format(args.outfile))
