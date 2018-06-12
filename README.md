# UIUC cPanel Ansible Example

This playbook demonstrates how to use the Technology Services cPanel
API Ansible module (cpanel_api). This module doesn't follow the
Ansible guidelines for module development because it exposes the raw
API instead of wrapping various operations in their own modules.
However, the cPanel API is extrememly large and developing individual
modules would take some time. We offer this as an intermediate
solution.

## Setup

Place the `cpanel_api.py` file in the `library/` folder of your
playbook or role. Because your inventory is managing the accounts
on our server and not the server itself, you will probably want to
use the account primary domain as the host and override the `ansible_host`
and `ansible_user` value.

Example `inventores/hosts.yml` for three accounts:

```yaml
---
all:
    hosts:
        itpfansibledev.web.illinois.edu:
            ansible_user: itpfansbledev
        itpfansibletest.web.illinois.edu:
            ansible_user: itpfansibletest
        itpfansibleprod.web.illinoiw.edu:
            ansible_user: itpfansibleprod
    vars:
        ansible_host: web.illinois.edu
```

In the playbook, you should turn off `gather_facts` unless you need to
use one of them. Again, you are managing only the account and not the
server. The facts ansible gathers will be generally useless and slow
down your playbook.

This example contains a `myapp` role. Generally, you will want to make
your app a role so that its tasks can be shared between the multiple
accounts. We will customize each account by providing variables to
the role.

In this example there are several `myapp` roles. This is used to show
a progression of stages as we make the role more complex. The `myapp_base`
role resets the account.

Example `myapp.yml` playbook for three accounts:

```yaml
---
- hosts: itpfansibledev.web.illinois.edu
  gather_facts: false
  roles:
      - role: myapp
- hosts: itpfansibletest.web.illinois.edu
  gather_facts: false
  roles:
      - role: myapp
- hosts: itpfansibleprod.web.illinois.edu
  gather_facts: false
  roles:
      - role: myapp
```

## cPanel API Usage

The module makes use of the [UAPI](https://documentation.cpanel.net/display/DD/Guide+to+UAPI)
and [cPanel API 2](https://documentation.cpanel.net/display/DD/Guide+to+cPanel+API+2)
modules and functions. You should prefer to use the UAPI over cPanel API 2,
but not all functions have been implemented in the UAPI.

There are other cPanel API's available, including WHM API 1 (which might
be useful to resellers). This example does not cover them but the basic
principals are the same.

An example of the cpanel_api module usage:

```yaml
- name: example cpanel_api usage
  cpanel_api:
      version: uapi
      module: APIModuleName
      function: APIFunctionName
      args:
          key1: value1
          key2: value2
  register: api_result
```

Parameters:
- *version* (optional): the API you are using. Valid values are `uapi`,
    `cpapi1`, `cpapi2`, `cpapi3`, `whmapi0`, and `whmapi1`.
    **Default**: `uapi`.
- *module*: the API module that contains the function. This value can be
    found in the documentation for the function.
- *function*: the API function to call. This value can be found in the
    documentation.
- *args*: key/value dictionary of arguments to pass to the function. The
    documentation states that arguments must be URL encoded, but the
    module will do this for you. If you need to specify the same key
    multiple times then append `-N` where `N` is an increasing
    integer (1, 2, 3, etc).
- *account* (optional): the account name to make this call as. This is
    only useful if you are a reseller logged into the reseller
    account, trying to perform an operation for an account you own.
    **Default**: current account.

Registering the output of an API call often gives you useful information
for later tasks. These keys are available in registered variables:

Output:
- *result*: the API call result, contained in the `result` or `cpanelresult`
    keys of the API output. The contents of the result depends on the
    API function called.
- *data*: the returned API call data, contained in the `data` key of
    the result. The contents of the data depends on the API function
    called. The data element is generally only available if the call
    succeeded.
- *stdout*: the raw string output from the API call, which should be
    a JSON document. This is the value that is parsed and used to fill
    in the `result` and `data` keys.
- *stderr*: the raw string error output from the API call.
- *rc*: the return code of the API command. This is not useful to detect
    failures in the API function, only failures in actually executing
    the command. Failure of the task depends on the contents of `result`.
- *start*, *end*, *delta*: the timestamps of the start and end of the
    command call, and also the amount of time that elapsed.
- *cmd*: the raw command that was executed. This might be useful for
    debugging problems.

The jmsepath module will help you break down the data in the `data` key
of successful calls. This example playbook makes use of the jmsepath
python module.
