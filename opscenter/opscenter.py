#!/usr/bin/env python
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from time import gmtime, strftime

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OpsCenter:
    def __init__(self, user, password, host='127.0.0.1', port=443, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.connection = 'http'
        if self.port == 443:
            self.connection = 'https'
        self._login(user, password)

    def _log(self, msg):
        if self.verbose:
            print 'OpsCenter:: {}'.format(msg)

    def _login(self, user, password):
        data = {'username': user, 'password': password}
        api_endpoint = '{}://{}:{}/login'.format(self.connection, self.host, self.port)
        r = requests.post(api_endpoint, data=data, verify=False)
        if r.status_code == 200:
            sessionid = json.loads(r.text)
            sessionid = sessionid['sessionid']
            session = requests.Session()
            session.headers.update(
                {
                    'opscenter-session': sessionid,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            session.verify = False
            self.session = session
            self._log('Logged In')
            return True
        else:
            raise ValueError('Login failed! Status Code: {}'.format(r.status_code))

    def _post(self, action, data):
        api_endpoint = '{}://{}:{}/{}'.format(self.connection, self.host, self.port, action)
        self._log('POST: {}'.format(api_endpoint))
        r = self.session.post(api_endpoint, data=data, verify=False)
        return r

    def _put(self, action, data):
        api_endpoint = '{}://{}:{}/{}'.format(self.connection, self.host, self.port, action)
        self._log('PUT: {}'.format(api_endpoint))
        r = self.session.put(api_endpoint, data=data, verify=False)
        return r

    def _get(self, action):
        api_endpoint = '{}://{}:{}/{}'.format(self.connection, self.host, self.port, action)
        self._log('GET: {}'.format(api_endpoint))
        r = self.session.get(api_endpoint, verify=False)
        return r

    def _delete(self, action):
        api_endpoint = '{}://{}:{}/{}'.format(self.connection, self.host, self.port, action)
        self._log('DELETE: {}'.format(api_endpoint))
        r = self.session.delete(api_endpoint, verify=False)
        return r

    def get_clusters(self, singularize=True):
        clusters = []
        r = self._get('cluster-configs')
        cass_clusters = json.loads(r.text)
        for cluster in cass_clusters:
            clusters.append(cluster)
        if len(clusters) == 1 and singularize:
            return clusters[0]
        else:
            return clusters

    def get_cluster_nodes(self, cluster_name):
        nodes = []
        api_endpoint = '{}/nodes'.format(cluster_name)
        r = self._get(api_endpoint)
        cassandra_nodes = json.loads(r.text)
        for node in cassandra_nodes:
            nodes.append(node)
        return nodes

    def update_admin_user(self, password, old_password='admin'):
        data = {'password': password, 'old_password': old_password}
        r = self._put('users/admin', data=json.dumps(data))
        if r.status_code == 200:
            return 'Admin user password updated'
        else:
            return 'Admin user password not updated! - Response Code: {} - Body: {}'.format(r.status_code, r.text)

    def create_role(self, role, role_data):
        role_data = json.dumps(role_data)
        r = self._post('permissions/roles/{}'.format(role), role_data)
        if r.status_code == 200:
            return 'Role {} Created'.format(role)
        else:
            error = json.loads(r.text)
            return 'Unable to create role. Status Code: {}. Error Message:{}'.format(r.status_code, error['message'])

    def list_roles(self):
        r = self._get('permissions/roles')
        response = json.loads(r.text)
        roles = []
        for role in response:
            roles.append(role['role'])
        return roles

    def list_role_permissions(self, role):
        r = self._get('permissions/roles/{}'.format(role))
        response = json.loads(r.text)
        if r.status_code == 200:
            return response
        else:
            return response['message']

    def delete_role(self, role):
        r = self._delete('permissions/roles/{}'.format(role))
        if r.status_code == 200:
            return '{} Role Deleted'.format(role)

    def create_user(self, user, password, role):
        data = {'password': password, 'role': role}
        new_user_uri = 'users/{}'.format(user)
        data = json.dumps(data)
        r = self._post(new_user_uri, data)
        if r.status_code == 200:
            return 'Added User: {}'.format(user)
        else:
            error = json.loads(r.text)
            return 'Unable to add user. Error: {} Status Code: {}'.format(error['message'], r.status_code)

    def list_users(self):
        r = self._get('users')
        return json.loads(r.text)

    def create_backup_destination(self, cluster_id, access_key, access_secret, path, provider):
        data = {'access_key': access_key, 'access_secret': access_secret, 'path': path, 'provider': provider,
                'server_side_encryption': 'true'}
        backup_uri = '{}/backups/destinations'.format(cluster_id)
        r = self._post(backup_uri, json.dumps(data))
        if r.status_code == 200:
            print 'Successfully added backup destination: {}'.format(provider)
            response = json.loads(r.text)
            return response['request_id']

    def get_backup_destinations(self, cluster_id):
        r = self._get('{}/backups/destinations'.format(cluster_id))
        return r.text

    def create_backup_schedule(self, cluster_id, run_time, retention):
        first_run = strftime("%Y-%m-%d", gmtime())
        data = {'first_run_date': first_run, 'first_run_time': run_time, 'timezone': 'US/Eastern', 'interval': 1,
                'interval_unit': 'days',
                'job_params': {'type': 'backup', 'keyspaces': [], 'cleanup_age': retention, 'cleanup_age_unit': 'days',
                               'destinations': {}}}
        job_uri = '{}/job-schedules'.format(cluster_id)
        r = self._post(job_uri, json.dumps(data))
        if r.status_code == 201:
            return 'Created Scheduled Backup. Start Date: {}, Start Time: {}, Retention: {} days, Job ID: {}'.format(
                first_run,
                run_time,
                retention, r.text)
        else:
            return r.status_code, r.text

    def delete_scheduled_backup(self, cluster_id, backup_id):
        job_uri = '{}/job-schedules/{}'.format(cluster_id, backup_id)
        r = self._delete(job_uri)
        if r.status_code == 200:
            print 'Backup Job {} deleted'.format(backup_id)

    def get_scheduled_backups(self, cluster_id):
        r = self._get('{}/job-schedules'.format(cluster_id))
        scheduled_jobs = json.loads(r.text)
        backups = []
        for job in scheduled_jobs:
            if job['job_params']['type'] == 'backup':
                backups.append(job)
        if len(backups) == 0:
            return 'No scheduled backups'
        else:
            return backups

    def get_bp_jobs(self, cluster_name_or_id):
        r = self._get('{}/job-schedules'.format(cluster_name_or_id))
        scheduled_jobs = json.loads(r.text)
        # On error:
        # {u'brief': u'error',
        #  u'message': u"There are no clusters with name or ID '378289d8-2960-4f12-a842-1d91773e66d4'",
        #  u'type': u'NoSuchCluster'}
        bp_jobs = []
        for job in scheduled_jobs:
            if job['job_params']['type'] != 'backup':
                bp_jobs.append(job)
        if len(bp_jobs) == 0:
            return 'No Best Practice Jobs found'
        else:
            return bp_jobs

    def get_backup_activity(self, cluster_name_or_id, count=16):
        r = self._get('{}/backup-activity?count={}'.format(cluster_name_or_id, count))
        ba = json.loads(r.text)
        return ba

    def get_cluster_storage(self, cluster_id):
        r = self._get('{}/storage-capacity'.format(cluster_id))
        return r.text
