#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function, unicode_literals
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cpanel_api
short_description: Executes a cPanel API function
version_added: 2.4.2
description:
    - The C(cpanel_api) module calls one of the cPanel API functions via
      a command line utility and provides the results back.
    - The given function will be executed on all selected nodes. It will not be
      processed through the shell, so variables like C($HOME) and operations
      like C("<"), C(">"), C("|"), C(";") and C("&") will not work (use the M(shell)
      module if you need these features).
options:
    version:
        description:
            - Name of the API version to use. Valid values are C(uapi), C(cpapi1),
              C(cpapi2), C(cpapi3), C(whmapi0), and C(whmapi1).
        default: uapi
        required: false
    account:
        description:
            - Name of the cPanel account to run this as. Only useful for resellers
              who are logged into their reseller account, or for root.
        required: false
    module:
        description:
            - Name of the cPanel module that contains the function being called.
        required: true
    function:
        description:
            - Name of the cPanel function in the module to call.
        required: true
    args:
        description:
            - Dictionary of arguments to pass to the function. Each argument
              is a key and a value for that key. Arguments that need to be
              specified multiple times should be appended with C(-N) where
              C(N) are increasing numbers.
            - Argument values will be url escaped by this module, so do not
              escape them youself.
        type: dict
        default: '{}'
        required: false
notes:
    -  If you want to run a command through the shell (say you are using C(<), C(>), C(|), etc), you actually want the M(shell) module instead.
       The C(cpanel_api) module is much more secure as it's not affected by the user's environment.
author:
    - Stephen J. Butler
'''

EXAMPLES = '''
- name: create a database user
  cpanel_api:
    module: Mysql
    function: create_user
    args:
        name: foo_test1
        password: changeme
  register: create_result
'''

import datetime
import glob
import json
import os
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import six
from ansible.module_utils.six.moves.urllib_parse import quote as urlquote


def main():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(default='uapi', choices=['uapi', 'cpapi1', 'cpapi2', 'cpapi3', 'whmapi0', 'whmapi1']),
            account=dict(required=False),
            module=dict(default='', required=False),
            function=dict(required=True),
            args=dict(default=dict(), type='dict', required=False),
        )
    )

    cp_version = module.params['version']
    cp_account = module.params['account']
    cp_module = module.params['module']
    cp_function = module.params['function']
    cp_args = module.params['args']

    args = [
        cp_version,
        '--output=json',
    ]

    if cp_account:
        args.append('--user={user}'.format(user=cp_account))

    if not cp_version in ('whmapi0', 'whmapi1'):
        if not cp_module:
            module.fail_json(msg='api version requires the module argument')
        args.append(cp_module)
    args.append(cp_function)

    for k, v in six.iteritems(cp_args):
        args.append('{name}={value}'.format(
            name=k,
            value=urlquote(v),
        ))

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(args, use_unsafe_shell=False, encoding=None)

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = b''
    if err is None:
        err = b''

    out_json = json.loads(out, encoding='utf-8')

    out_result = out_json
    if 'result' in out_json:
        out_result = out_json['result']
    elif 'cpanelresult' in out_json:
        out_result = out_json['cpanelresult']

    out_data = out_result.get('data', None)

    result = dict(
        cmd=args,
        result=out_result,
        data=out_data,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)
    elif cp_version == 'uapi' and out_result.get('errors', None):
        module.fail_json(msg='errors returned: {errors}'.format(errors='; '.join(out_result['errors'])))
    elif cp_version in ('cpapi1', 'cpapi2', 'cpapi3') and out_result.get('error', None):
        module.fail_json(msg='errors returned: {errors}'.format(errors=out_result['error']))
    elif cp_version in ('whmapi0', 'whmapi1') and out_result['metadata']['result'] == 0:
        module.fail_json(msg='errors returned: {errors}'.format(errors=out_result['metadata']['reason']))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
