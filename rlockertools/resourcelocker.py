from requests.exceptions import ConnectionError, ReadTimeout
from rlockertools.exceptions import BadRequestError, TimeoutReachedForLockingResource
from rlockertools.utils import prettify_output
import requests
import json
import time
import logging


logger = logging.getLogger('__name__')

class ResourceLocker:
    def __init__(self, instance_url, token):
        self.instance_url = instance_url
        self.token = token

        self.check_connection()

        self.endpoints = {
            'resources': f'{self.instance_url}/api/resources',
            'retrieve_resource': f'{self.instance_url}/api/resource/retrieve_entrypoint/',
            'resource': f'{self.instance_url}/api/resource/',
            'rqueue': f'{self.instance_url}/api/rqueue/',
            'rqueues': f'{self.instance_url}/api/rqueues',
        }

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }

    def check_connection(self):
        '''
        Checks Connection to the provided URL after initialization

        :return: None
        :raises: Connection Error
        '''
        req = requests.get(self.instance_url)
        if req.status_code == 200:
            print({'CONNECTION': 'OK'})
            return
        else:
            # Raise Connection Error if no 200
            raise ConnectionError

    def find_resource(self, search_string, signoff, priority, link=None, timeout=None):
        '''

        :param search_string:
        :param signoff:
        :param priority:
        :param link:
        :param timeout:
        :return:
        '''
        final_endpoint = self.endpoints['retrieve_resource'] + search_string
        data = {
            "priority": priority,
            "signoff": signoff,
        }
        if link:
            data['link'] = link

        data_json = json.dumps(data)

        try:
            req = requests.put(final_endpoint, headers=self.headers, data=data_json, timeout=timeout)
            return req

        except ReadTimeout:
            raise TimeoutReachedForLockingResource

    def __lock(self, resource, signoff):
        '''
        Method that will lock the requested resource
        :param resource: Resource to lock
        :param signoff: A message to write when the requested resource
            is about to lock
        :return: Response after the PUT request
        '''
        lockable_resource = dict(resource)
        lockable_resource['is_locked'] = True
        lockable_resource['signoff'] = signoff

        final_endpoint = self.endpoints['resource'] + lockable_resource['name']
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        return req

    def release(self, resource):
        '''
        Method that will release the requested resource
        :param resource: Resource to release
        :return: Response after the PUT request
        '''
        lockable_resource = dict(resource)
        lockable_resource['is_locked'] = False

        final_endpoint = self.endpoints['resource'] + lockable_resource['name']
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        if req.status_code == 200:
            print(f"Released {resource['name']} successfully!")
            return req
        else:
            print(f"There were some errors from the Resource Locker server:")
            prettify_output(req.text)

    def all(self):
        '''
        Display all the resources
        :return: Response in Dictionary
        '''
        req = requests.get(self.endpoints['resources'], headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary:
            req_dict = json.loads(req.text.encode('utf8'))
            return req_dict
        else:
            prettify_output(req.text)
            raise BadRequestError

    def filter_lockable_resource(self, lambda_expression):
        '''

        :param lambda_expression:
            Example:
                lambda x: getattr(x, 'is_locked') == False
        :return:
        '''
        return filter(lambda_expression, self.all())

    def abort_queue(self, queue_id, abort_msg=None):
        '''
        A method to send a POST request to abort the queue that was created, and expected
            to have an associated lockable resource
        We do this from the client side for now.
        :return: req
        '''
        final_endpoint = self.endpoints['rqueue'] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            data_json = json.dumps(
                {
                    'status': 'ABORTED',
                    'description': abort_msg,
                }
            )

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            return req

    def change_queue(self, queue_id, status, description=None):
        '''
        A method to send a POST request to change the status of the queue.
        :return: req
        '''
        final_endpoint = self.endpoints['rqueue'] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:

            data = {
                "status" : status,
            }
            if description:
                data['description'] = description

            data_json = json.dumps(data)

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            return req

        return req

    def get_queues(self, status=None):
        final_endpoint = self.endpoints['rqueues'] + f'?status={status}' if status else self.endpoints['rqueues']
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary
            req_dict = json.loads(req.text.encode('utf8'))
            return req_dict

    def get_queue(self, queue_id):
        '''
        Return queue JSONIFIED by the given queue_id
        :param queue_id:
        :return:
        '''
        final_endpoint = self.endpoints['rqueue'] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            return req.json()

        return None

    def wait_until_status(self, queue_id, status,
                          interval=15, attempts=120, silent=True):
        '''
        A method that uses multiple retries until a status of queue is achieved
        :param queue_id:
        :param status:
        :param interval:
        :param attempts:
        :param silent: If timeout is reached (attempts * interval), then
            it will silently return None rather than raising Exception.
        :return:
        '''
        for attempt in range(attempts):
            queue_to_check = self.get_queue(queue_id)
            if not queue_to_check:
                raise Exception(f'Queue {queue_id} does not exist on the server!')

            if queue_to_check.get('status') == status:
                return queue_to_check

            else:
                # This needs to log, to automatically stream the output even though the process
                # is running on CI/CD platforms like Jenkins.
                logger.info(f"{queue_id} is not in status {status} yet"
                      f"More info about the queue: \n"
                      f"{self.instance_url}\pendingrequests")

                time.sleep(interval)
        else:
            if silent:
                return None
            else:
                raise Exception("Timeout Reached! \n"
                                f"Status of the queue is not {status}!")


    def get_lockable_resources(
            self, free_only=True,
            label_matches=None, name=None, signoff=None
    ):
        if not signoff:
            # Lets first design the final endpoint:
            final_endpoint = self.endpoints['resources'] + f'?free_only={str(free_only).lower()}&'
            if label_matches:
                final_endpoint = f"{final_endpoint}label_matches={label_matches}"
            if name:
                final_endpoint = f"{final_endpoint}name={name}"
        else:
            final_endpoint = self.endpoints['resources'] + f'?signoff={signoff}'

        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary
            req_dict = json.loads(req.text.encode('utf8'))
            return req_dict

        return req

    def lock_resource(self, resource, signoff, link=None):
        '''
        Method that will lock the requested resource
        :param resource: Resource to lock
        :param signoff: A message to write when the requested resource
            is about to lock
        :return: Response after the PUT request
        '''
        lockable_resource = dict(resource)
        lockable_resource['is_locked'] = True
        lockable_resource['signoff'] = signoff
        if link:
            lockable_resource['link'] = link

        final_endpoint = self.endpoints['resource'] + lockable_resource['name']
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        return req