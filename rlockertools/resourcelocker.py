from requests.exceptions import ConnectionError
from rlockertools.exceptions import BadRequestError
from rlockertools.utils import prettify_output
import requests
import json
import time

class ResourceLocker:
    def __init__(self, instance_url, token):
        self.instance_url = instance_url
        self.token = token

        self.check_connection()

        self.endpoints = {
            'resources'         : f'{self.instance_url}/api/resources',
            'retrieve_resource' : f'{self.instance_url}/api/resource/retrieve/',
            'resource'      : f'{self.instance_url}/api/resource/',
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

    def __retrieve(self, search_string):
        '''
        Method that will return one resource locker Dict object at a time
        :param search_string: String to search by, could be the name or the label of the resource
        :return: Request object
        '''
        final_endpoint = self.endpoints['retrieve_resource'] + search_string
        req = requests.get(final_endpoint, headers=self.headers)
        return req



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

    def queued_lock(self,search_string, signoff, interval=60):
        '''

        :param search_string: The string to search for when we attempt locking,
            will try to find by label or name
        :param signoff: A unique signoff for the resources that are going to be locked
        :param interval: How much time to wait after each attempt, default is 60
        :return:
        '''
        while True:
            retrieve_attempt = self.__retrieve(search_string)
            if retrieve_attempt.status_code == 206:
                print(f"Resources with the requested search_string ({search_string}) are locked! \n"
                      f"Waiting {interval} seconds before next try!")
                time.sleep(interval)

            elif retrieve_attempt.status_code == 200:
                print(f"Available resource found with name/label : {search_string} \n"
                      "Trying to lock...")
                lockable_resource_obj = json.loads(retrieve_attempt.text.encode('utf8'))

                attempt_lock = self.__lock(resource=lockable_resource_obj, signoff=signoff)

                if attempt_lock.status_code == 200:
                    attempt_lock_obj = json.loads(attempt_lock.text.encode('utf8'))
                    print(f"Locked {attempt_lock_obj['name']} successfully!")

                    return attempt_lock_obj
                else:
                    print(f"There were some errors locking the requested resource:")
                    prettify_output(attempt_lock.text)

                    raise BadRequestError

            else:
                print("There were some errors retrieving a free resource:")
                prettify_output(retrieve_attempt.text)
                raise BadRequestError