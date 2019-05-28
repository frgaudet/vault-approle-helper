#!/usr/bin/python3
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    <http://www.gnu.org/licenses/>.
#
# F-Gaudet 2019

import hvac
import yaml
import urllib3
import sys
import json
import argparse
import os
from prettytable import PrettyTable

urllib3.disable_warnings()


def __get_config_yaml(yaml_file):
    '''Get the vault configuration from file.

    Args:
        yaml_file (str) : The config filename

    Returns:
        YAML object containing the configuration
    '''
    try:
        with open(yaml_file, 'r') as stream:
            return yaml.load(stream)
    except IOError:
        print("{'error': 'config file %s no found'}" % yaml_file)
        sys.exit(1)
    except yaml.YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print("{'yaml error': 'position: (%s:%s)'}" % (mark.line+1, mark.column+1))
        sys.exit(1)


def create_secret_id(client, role_name, hostname):
    '''Create a secret_id for a given role. Add hostname as metadata addition.

    Args:
        client (hvac_client): hvac_client instance
        role_name (str) : Role name
        hostname (str): Hostname

    Returns:
        Secret_id
    '''
    METADATA_HEADERS={ 'hostname': hostname }
    secret_id_accessor=__get_secret_id_accessor(client, role_name, hostname)
    if secret_id_accessor is None:
        try:
            ret=client.create_role_secret_id(role_name=role_name,meta=METADATA_HEADERS )
        except Exception as e:
           print("{'error': '%s'}" % e)
        else:
           print("%s" % ret['data'].get('secret_id'))
    else:
        print("{'error': 'hostname exists'}")

def list_secret(client, role_name):
    try:
        vault_data = client.list('auth/approle/role/{0}/secret-id'.format( role_name) )
    except hvac.exceptions.Forbidden:
        print("{'error': 'forbidden'}")
        return
    except:
        print("Role %s does not exist. Here the list :" % role_name)
        role_list = client.list('auth/approle/role')['data']['keys']
        field_names = ['Roles']
        table = PrettyTable()
        table.field_names = field_names
        table.align = 'l'
        for i in role_list:
            table.add_row([i
            ])
        print(table)
        sys.exit(2)
    if vault_data is not None:
        field_names = ['hostname', 'secret_id_accessor']
        table = PrettyTable()
        table.field_names = field_names
        table.align = 'l'
        for i in vault_data['data']['keys']:
            try:
                table.add_row([
                    client.get_role_secret_id_accessor(role_name,i)['data']['metadata'].get('hostname'),
                    i
                ])
            except:
                print("{'error': 'listing failed'}")
                return
        print(table)
    else:
        print("{'error': 'no secret found for %s'}"  % role_name)

def __get_secret_id_accessor(client, role_name, hostname):
    '''Get the secret_id_accessor for a given hostname.

    Args:
        client (hvac_client): hvac_client instance
        role_name (str) : Role name
        hostname (str): Hostname

    Returns:
        Secret_id
    '''
    vault_data = client.list('auth/approle/role/{0}/secret-id'.format( role_name))
    if vault_data is not None:
        for i in vault_data['data']['keys']:
            ret = client.get_role_secret_id_accessor(role_name,i)['data']['metadata'].get('hostname')
            if (ret == hostname):
                return client.get_role_secret_id_accessor(role_name,i)['data']['secret_id_accessor']


def delete_secret_id_from_hostname(client, role_name, hostname):
    '''Delete a secret_id for a given hostname

    Args:
        role_name (str) : Role name
        hostname (str): Hostname

    Returns:
        Secret_id
    '''
    secret_id_accessor=__get_secret_id_accessor(client, role_name, hostname)
    if secret_id_accessor is not None:
        try:
            client.delete_role_secret_id_accessor(role_name, secret_id_accessor)
        except Exception as e:
            print("{'error': '%s'}" % e)
            return
    else:
        print("{'error': 'no secret found for %s'}"  % hostname)
        return
    print("{'ok': 'delete succeeded'}")


def delete_secret_id_from_secret_id_accessor(client, role_name, secret_id_accessor):
    '''Delete a secret_id for a given secret_id_accessor

    Args:
        client (hvac_client): hvac_client instance
        role_name (str) : Role name
        hostname (str): Hostname

    Returns:
        Secret_id
    '''
    try:
        client.delete_role_secret_id_accessor(role_name, secret_id_accessor)
    except Exception as e:
        print("{'error': '%s'}" % e)
    else:
        print("{'ok': 'delete succedded'}")


def __get_auth(verify):
    '''Authenticate to vault server. Use /etc/vault/config.yaml file.
    Override settings with VAULT_URL and VAULT_TOKEN environment variables.

    Args:
        verify (boolean) : SSL cert verification

    Returns:
        hvac.Client() instance
    '''
    try:
        client = hvac.Client(url=os.environ['VAULT_URL'], verify=verify)
        client.token = os.environ['VAULT_TOKEN']
    except:
        pass
    else:
        return client
    config = __get_config_yaml('/etc/vault/config.yaml')
    try:
        client = hvac.Client(url=config['url'], verify=verify)
        client.auth_approle(config['role_id'], config['secret_id'])
    except:
        print("{'error': 'login failed'}")
        sys.exit(1)
    return client


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vault Approle Helper')

    parser.add_argument('role_name', help="The role you want to act on")
    parser.add_argument(
        '-k',
        action='store_false',
        help="Don't check SSL certificate")
    subparsers = parser.add_subparsers(dest='subcommand')

    parser_list = subparsers.add_parser('list')

    parser_delete = subparsers.add_parser('delete')
    parser_delete.add_argument(
        'hostname',
        help='Hostname')

    delete_from_secret = subparsers.add_parser('delete_from_secret')
    delete_from_secret.add_argument(
        'secret_id_accessor',
        help='Secret_id accessor')

    parser_create = subparsers.add_parser('create')
    parser_create.add_argument(
        'hostname',
        help='Hostname')

    args = parser.parse_args()

    if args.subcommand == 'list':
        client=__get_auth(args.k)
        list_secret(client,
                    args.role_name)

    if args.subcommand == 'delete':
        client=__get_auth(args.k)
        delete_secret_id_from_hostname(client,
                    args.role_name,
                    args.hostname)

    if args.subcommand == 'delete_from_secret':
        client=__get_auth(args.k)
        delete_secret_id_from_secret_id_accessor(client,
                   args.role_name,
                   args.secret_id_accessor)

    if args.subcommand == 'create':
        client=__get_auth(args.k)
        create_secret_id(client,
                   args.role_name,
                   args.hostname)
