from requests.exceptions import ConnectionError, ReadTimeout
from rlockertools.exceptions import BadRequestError, TimeoutReachedForLockingResource
from rlockertools.utils import prettify_output
import requests
import json

class ResourceLocker:
    def __init__(self, instance_url, token):
        self.instance_url = instance_url
        self.token = token

        self.check_connection()

        self.endpoints = {
            'resources'         : f'{self.instance_url}/api/resources',
            'retrieve_resource' : f'{self.instance_url}/api/resource/retrieve_entrypoint/',
            'resource'          : f'{self.instance_url}/api/resource/',
            'rqueue'            : f'{self.instance_url}/api/rqueue/',
            'rqueues'           : f'{self.instance_url}/api/rqueues',
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
            print({'CONNECTION' : 'OK'})
            return
        else:
            #Raise Connection Error if no 200
            raise ConnectionError

    def retrieve_and_lock(self, search_string, signoff, priority, link=None, timeout=None):
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
            "priority" : priority,
            "signoff" : signoff,
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
            #json.loads returns it to a dictionary:
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

    def get_lockable_resource(self, lambda_expression):
        '''
        Uses next to return the first value only after using the filter_lockable_resource
            So we don't have to call it each time
        :param lambda_expression:
        :return:
        '''
        return next(self.filter_lockable_resource(lambda_expression=lambda_expression))

    def get_current_queue(self):
        '''
        Get the latest current queue that is created, without filtering its status,
            just the latest queue ID
        :return rqueue JSON object
        '''
        req = requests.get(self.endpoints['rqueues'], headers=self.headers)
        if req.status_code == 200:
            #json.loads returns it to a dictionary
            req_dict = json.loads(req.text.encode('utf8'))
            return req_dict
        else:
            print(f"There were some errors from the Resource Locker server:")
            prettify_output(req.text)

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
                    'status' : 'ABORTED',
                    'description' : abort_msg,
                }
            )

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            return req

