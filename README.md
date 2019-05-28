# Vault Approle Helper

This tool allow us to manage role secret_id. It delivers a secret_id the first time a VM or a container is launched. Each container or VM has a specific role, as such for each secret_id we add the hostname as a metadata to easily identify if a secret has been issued for this specific hostname. When we remove the VM or container, we can easily remove the secret_id.

It uses 2 differents auth method : approle or token based. I usually use the approle method if this script is intend to be run automatically (create policy only), and token based if I want to run it manually with an admin scoped token..

## Prerequisites

You have a running Vault installation, with installed policies and roles.

Here, for example, I'll use the role `my-role`, and I 'll use an admin token given with `vault login -method=ldap username=fred`.

## Installation

```bash
pip3 install -r requirements.txt
```

## Config file

located in `/etc/vault/config.yaml` and containing the following :

```bash
url: https://vault.service.consul:8200
role_id: 00000000-0000-0000-0000-000000000001
secret_id: 00000000-0000-0000-0000-000000000002
```

These settings could be overridden with env variables if you want to use an existing token :

```bash
export VAULT_TOKEN=00000000-0000-0000-0000-000000000003
export VAULT_URL=https://vault.service:8200
```

## Usage

```bash
usage: vault-approle-helper.py [-h] [-k]
             role_name {list,delete,create,delete_from_secret} ...

Vault Approle Helper

positional arguments:
  role_name             The role you want to act on
  {list,delete,create,delete_from_secret}

optional arguments:
  -h, --help            show this help message and exit
  -k                    Don't check SSL certificate
```


## Create secret_id

Create a new secret_id for a given role :

```bash
fred@mbp:~# ./vault-approle-helper.py -k my-role create test
60e18b79-71ce-afe2-070c-a5fc97b93a36
```

## List all secrets for a given role

  Give a role name and add an action :

```bash
fred@mbp:~# ./vault-approle-helper.py -k my-role list
+----------+--------------------------------------+
| hostname | secret_id_accessor                   |
+----------+--------------------------------------+
| test     | 45d5af5e-733a-092a-201d-3d8b601b347c |
+----------+--------------------------------------+
```

If the role name doesn't exists, you'll get the list of existing roles.

```bash
fred@mbp:~# ./vault-approle-helper.py -k my-role-d list
Role my-role-d does not exist. Here the list :
+----------------------+
| role                 |
+----------------------+
| my-role              |
+----------------------+
```

## Delete secret_id

Delete a secret_id for a given hostname :

```bash
fred@mbp:~# ./vault-approle-helper.py -k my-role delete test
{'ok': 'delete succeeded'}
```

## Delete secret_id from secret_id_accessor

Delete a secret_id for a given secret_id_accessor :

```bash
fred@mbp:~# ./vault-approle-helper.py -k my-role delete_from_secret 45d5af5e-733a-092a-201d-3d8b601b347c
{'ok': 'delete succeeded'}
```
