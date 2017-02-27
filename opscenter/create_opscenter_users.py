#!/usr/bin/env python

# Salt Managed

import argparse
from opscenter import OpsCenter


def main(args):
    try:
        opscenter = OpsCenter(user=args['admin-user'], password=args['admin-pass'], verbose=args['verbose'])
    except ValueError as e:
        if args['action'] == 'update_admin':
            opscenter = OpsCenter(user=args['admin-user'], password='admin', verbose=args['verbose'])
        else:
            raise e
    cluster = opscenter.get_clusters()
    if args['action'] == 'update_admin':
        return opscenter.update_admin_user(args['admin-pass'])
    elif args['action'] == 'add-users':
        return opscenter.create_user(args['user'], args['password'], args['role'])
    elif args['action'] == 'create-role':
        role_data = {
            cluster: {
                "View Cluster": True,
                "Alerting": True,
                "Node Start and Stop": False,
                "Backup and Restore": True,
            }
        }
        return opscenter.create_role(args['role'], role_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Update OpsCenter Users'
    )

    parser.add_argument(
        '-a', '--action',
        choices=['update_admin', 'add-users', 'create-role'],
        required=True,
        default='add-users',
        dest='action',
    )
    parser.add_argument(
        '--admin-user',
        required=True,
        dest='admin-user',
    )

    parser.add_argument(
        '--admin-pass',
        required=True,
        dest='admin-pass',
    )

    parser.add_argument(
        '-u', '--user',
        required=False,
        dest='user',
    )

    parser.add_argument(
        '-p', '--password',
        required=False,
        dest='password',
    )

    parser.add_argument(
        '-r', '--role',
        required=False,
        dest='role',
    )

    parser.add_argument(
        '-v', '--verbose',
        required=False,
        dest='verbose',
        action='store_true',
    )

    args = vars(parser.parse_args())

    print main(args)
