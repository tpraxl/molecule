#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os
import sys
import click
from molecule import api
from molecule import logger
from molecule import util
from molecule.command import base as command_base
from molecule.command.init import base

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


LOG = logger.get_logger(__name__)


class Role(base.Base):
    """
    .. program:: molecule init role --role-name foo

    .. option:: molecule init role --role-name foo

        Initialize a new role.

    .. program:: molecule init role --role-name foo --template path

    .. option:: molecule init role --role-name foo --template path

        Initialize a new role using ansible-galaxy and include default
        molecule directory. Please refer to the ``init scenario``
        command in order to generate a custom ``molecule`` scenario.
    """

    def __init__(self, command_args):
        self._command_args = command_args

    def execute(self):
        """
        Execute the actions necessary to perform a `molecule init role` and
        returns None.

        :return: None
        """

        role_name = self._command_args['role_name']
        role_directory = os.getcwd()
        msg = 'Initializing new role {}...'.format(role_name)
        LOG.info(msg)

        if os.path.isdir(role_name):
            msg = ('The directory {} exists. ' 'Cannot create new role.').format(
                role_name
            )
            util.sysexit_with_message(msg)

        try:
            cmd = ["ansible-galaxy", "init", "-v", "--offline", role_name]
            subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except Exception as e:
            util.sysexit_with_message(
                "Galaxy failed to create role: %s: %s" % (e, e.output)
            )

        scenario_base_directory = os.path.join(role_directory, role_name)
        templates = [
            api.drivers()[self._command_args['driver_name']].template_dir(),
            api.verifiers()[self._command_args['verifier_name']].template_dir(),
        ]
        for template in templates:
            self._process_templates(
                template, self._command_args, scenario_base_directory
            )
        self._process_templates('molecule', self._command_args, role_directory)

        role_directory = os.path.join(role_directory, role_name)
        msg = 'Initialized role in {} successfully.'.format(role_directory)
        LOG.success(msg)


@click.command()
@click.pass_context
@click.option(
    '--dependency-name',
    type=click.Choice(['galaxy']),
    default='galaxy',
    help='Name of dependency to initialize. (galaxy)',
)
@click.option(
    '--driver-name',
    '-d',
    type=click.Choice([str(s) for s in api.drivers()]),
    default='docker',
    help='Name of driver to initialize. (docker)',
)
@click.option(
    '--lint-name',
    type=click.Choice(['yamllint']),
    default='yamllint',
    help='Name of lint to initialize. (yamllint)',
)
@click.option(
    '--provisioner-name',
    type=click.Choice(['ansible']),
    default='ansible',
    help='Name of provisioner to initialize. (ansible)',
)
@click.option('--role-name', '-r', required=True, help='Name of the role to create.')
@click.option(
    '--verifier-name',
    type=click.Choice([str(s) for s in api.verifiers()]),
    default='testinfra',
    help='Name of verifier to initialize. (testinfra)',
)
def role(
    ctx,
    dependency_name,
    driver_name,
    lint_name,
    provisioner_name,
    role_name,
    verifier_name,
):  # pragma: no cover
    """ Initialize a new role for use with Molecule. """
    command_args = {
        'dependency_name': dependency_name,
        'driver_name': driver_name,
        'lint_name': lint_name,
        'provisioner_name': provisioner_name,
        'role_name': role_name,
        'scenario_name': command_base.MOLECULE_DEFAULT_SCENARIO_NAME,
        'subcommand': __name__,
        'verifier_name': verifier_name,
    }

    command_args['verifier_lint_name'] = api.verifiers()[verifier_name].default_linter

    r = Role(command_args)
    r.execute()
