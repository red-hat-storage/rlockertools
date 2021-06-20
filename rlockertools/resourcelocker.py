from requests.exceptions import ConnectionError, ReadTimeout
from rlockertools.exceptions import BadRequestError, TimeoutReachedForLockingResource
from rlockertools.utils import prettify_output
import requests
import datetime
import json
import time
import pprint as pp


class ResourceLocker:
    def __init__(self, instance_url, token):
        self.instance_url = instance_url
        self.token = token

        self.check_connection()

        self.endpoints = {
            "resources": f"{self.instance_url}/api/resources",
            "retrieve_resource": f"{self.instance_url}/api/resource/retrieve_entrypoint/",
            "resource": f"{self.instance_url}/api/resource/",
            "rqueue": f"{self.instance_url}/api/rqueue/",
            "rqueues": f"{self.instance_url}/api/rqueues",
        }

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}",
        }

    def check_connection(self):
        """
        Checks Connection to the provided URL after initialization

        :return: None
        :raises: Connection Error
        """
        req = requests.get(self.instance_url)
        if req.status_code == 200:
            print({"CONNECTION": "OK"})
            return
        else:
            # Raise Connection Error if no 200
            raise ConnectionError

    def find_resource(self, search_string, signoff, priority, link=None, timeout=None):
        """

        :param search_string:
        :param signoff:
        :param priority:
        :param link:
        :param timeout:
        :return:
        """
        final_endpoint = self.endpoints["retrieve_resource"] + search_string
        data = {
            "priority": priority,
            "signoff": signoff,
        }
        if link:
            data["link"] = link

        data_json = json.dumps(data)

        try:
            req = requests.put(
                final_endpoint, headers=self.headers, data=data_json, timeout=timeout
            )
            return req

        except ReadTimeout:
            raise TimeoutReachedForLockingResource

    def __lock(self, resource, signoff):
        """
        Method that will lock the requested resource
        :param resource: Resource to lock
        :param signoff: A message to write when the requested resource
            is about to lock
        :return: Response after the PUT request
        """
        lockable_resource = dict(resource)
        lockable_resource["is_locked"] = True
        lockable_resource["signoff"] = signoff

        final_endpoint = self.endpoints["resource"] + lockable_resource["name"]
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        return req

    def release(self, resource):
        """
        Method that will release the requested resource
        :param resource: Resource to release
        :return: Response after the PUT request
        """
        lockable_resource = dict(resource)
        lockable_resource["is_locked"] = False

        final_endpoint = self.endpoints["resource"] + lockable_resource["name"]
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        if req.status_code == 200:
            print(f"Released {resource['name']} successfully!")
            return req
        else:
            print(f"There were some errors from the Resource Locker server:")
            prettify_output(req.text)

    def all(self):
        """
        Display all the resources
        :return: Response in Dictionary
        """
        req = requests.get(self.endpoints["resources"], headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary:
            req_dict = json.loads(req.text.encode("utf8"))
            return req_dict
        else:
            prettify_output(req.text)
            raise BadRequestError

    def filter_lockable_resource(self, lambda_expression):
        """

        :param lambda_expression:
            Example:
                lambda x: getattr(x, 'is_locked') == False
        :return:
        """
        return filter(lambda_expression, self.all())

    def abort_queue(self, queue_id, abort_msg=None):
        """
        A method to send a POST request to abort the queue that was created, and expected
            to have an associated lockable resource
        We do this from the client side for now.
        :return: req
        """
        final_endpoint = self.endpoints["rqueue"] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            data_json = json.dumps(
                {
                    "status": "ABORTED",
                    "description": abort_msg,
                }
            )

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            pp.pprint(req.json())
            return req

        print(f"Something went wrong aborting the {queue_id} \n")
        pp.pprint(req.json())
        return req

    def change_queue(self, queue_id, status, description=None):
        """
        A method to send a POST request to change the status of the queue.
        :return: req
        """
        final_endpoint = self.endpoints["rqueue"] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:

            data = {
                "status": status,
            }
            if description:
                data["description"] = description

            data_json = json.dumps(data)

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            pp.pprint(req.json())
            return req

        print(f"Something went wrong changing {queue_id} \n")
        pp.pprint(req.json())
        return req

    def get_queues(self, status=None):
        final_endpoint = (
            self.endpoints["rqueues"] + f"?status={status}"
            if status
            else self.endpoints["rqueues"]
        )
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary
            req_dict = json.loads(req.text.encode("utf8"))
            return req_dict

    def get_queue(self, queue_id, verify_connection=False):
        """
        Return queue JSONIFIED by the given queue_id
        :param queue_id:
        :param verify_connection: Check the connection to the server before
            retrieving the JSON for the specific queue, False by default
        :return:
        """
        if verify_connection:
            self.check_connection()

        final_endpoint = self.endpoints["rqueue"] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            return req.json()

        return None

    def wait_until_finished(
        self,
        queue_id,
        interval=15,
        attempts=120,
        silent=False,
        abort_on_timeout=True,
        resume_on_connection_error=False,
    ):
        """
        A method that uses multiple retries until a status of queue is achieved
            Approach: return the queue obj as JSON if status is achieved.
            In any other case if failure/aborted or timeout,
                we raise Exception if silent=False.
            Or printing the message silently if silent=True.
        :param queue_id:
        :param interval: Time to wait in seconds between the attempts
        :param attempts: Number of the attempts to try
        :param silent: If timeout is reached (attempts * interval), then
            it will silently return None rather than raising Exception.
        :param abort_on_timeout: Aborts the queue if timeout is reached
        :param resume_on_connection_error: Do not interrupt the waiting, if in the middle of it
            we will have connection errors (server is down).

        :return queue as JSON response:
        """
        expected_status = "FINISHED"
        total_timeout_description = f"{attempts * interval} seconds"
        print(
            f"Waiting until status {expected_status}, timeout is set to {total_timeout_description}! \n"
            "If the queue is in INITIALIZING state for a while, "
            "be sure to check if your queue service is running! \n"
        )
        for attempt in range(attempts):
            try:
                queue_to_check = self.get_queue(
                    queue_id,
                    verify_connection=True
                )
                if not queue_to_check:
                    raise Exception(
                        f"Queue {queue_id} does not exist on the server! \n"
                        "Error is not recoverable, raising Exception \n"
                        "Please check the logs of the Django application! \n"
                        "Possible solutions: \n"
                        " - Please double check your search_string, that it matches to an existing label or name"
                    )
                # Once we passed through the check if queue exists, we should check continuously it's status:
                queue_status = queue_to_check.get("status")
                if queue_status == expected_status:
                    return queue_to_check

                else:
                    if queue_status in ["INITIALIZING", "PENDING"]:
                        print(
                            f"Queue {queue_id} is {queue_status} \n"
                            f"More info about the queue: \n"
                            f"{self.instance_url}/rqueues/{queue_id}"
                        )
                    elif queue_status in ["ABORTED", "FAILED"]:
                        err_msg = (
                            "Queue did NOT finish successfully \n"
                            f"Error is: \n {queue_to_check}"
                        )
                        if silent:
                            print(
                                err_msg,
                                "Timeout reached, "
                                "silent=true provided so no exception is raised",
                            )
                            return None
                        else:
                            raise Exception(err_msg)

                    self.beat_queue(queue_id)
                    time.sleep(interval)
            except ConnectionError as e:
                print(
                    "Connection Error to the specified URL! \n"
                    "Error is: \n"
                    f"{str(e)}"
                )
                # If there was a connection error while waiting for the achieved status,
                # the user might want to wait until the server is back up.
                if resume_on_connection_error:
                    # User decided to resume on connection error!
                    # We want to continuously show this message, in order to avoid iteration, and waste the attempts
                    # on connection errors.
                    while True:
                        print(
                            f"Will try again in {interval} seconds \n"
                            "NOTE: Timeout duration is paused! \n"
                            "You decided to wait if connection errors will occur, your queue "
                            f"will still have a timeout of {(attempts - attempt) * interval} seconds, once the resource locker server is back!"
                        )
                        time.sleep(interval)
                        try:
                            self.check_connection()
                            # If method did not raise, get out, server is up
                            break
                        except:
                            pass
                else:
                    raise
            except Exception as e:
                print("An unknown exception occured: \n"
                      f"{str(e)}")
                raise

        else:
            if abort_on_timeout:
                self.abort_queue(
                    queue_id=queue_id,
                    abort_msg="Timeout Reached for this queue. \n"
                    f"Attempts: {attempts} \n"
                    f"Interval: {interval} seconds \n"
                    f"Time Waited: {attempts * interval} seconds",
                )
            if silent:
                print("Timeout reached, silent=true provided so no exception is raised")
                return None
            else:
                raise Exception(
                    "Timeout Reached! \n"
                    f"Status of the queue is not {expected_status}!"
                )

    def get_lockable_resources(
        self, free_only=True, label_matches=None, name=None, signoff=None
    ):
        if not signoff:
            # Lets first design the final endpoint:
            final_endpoint = (
                self.endpoints["resources"] + f"?free_only={str(free_only).lower()}&"
            )
            if label_matches:
                final_endpoint = f"{final_endpoint}label_matches={label_matches}"
            if name:
                final_endpoint = f"{final_endpoint}name={name}"
        else:
            final_endpoint = self.endpoints["resources"] + f"?signoff={signoff}"

        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:
            # json.loads returns it to a dictionary
            req_dict = json.loads(req.text.encode("utf8"))
            return req_dict

        return req

    def lock_resource(self, resource, signoff, link=None):
        """
        Method that will lock the requested resource
        :param resource: Resource to lock
        :param signoff: A message to write when the requested resource
            is about to lock
        :return: Response after the PUT request
        """
        lockable_resource = dict(resource)
        lockable_resource["is_locked"] = True
        lockable_resource["signoff"] = signoff
        if link:
            lockable_resource["link"] = link

        final_endpoint = self.endpoints["resource"] + lockable_resource["name"]
        newjson = json.dumps(lockable_resource)

        req = requests.put(final_endpoint, headers=self.headers, data=newjson)
        return req

    def beat_queue(self, queue_id):
        '''
        Method that will write the datetime.utcnow() to the field of
            last_beat to the queue.
        This is useful to determine if there is still alive client
            that waits for the specific queue to being FINISHED
        :param queue_id:
        :return:
        '''
        final_endpoint = self.endpoints["rqueue"] + str(queue_id)
        req = requests.get(final_endpoint, headers=self.headers)
        if req.status_code == 200:

            data = {
                "last_beat": str(datetime.datetime.utcnow()),
            }

            data_json = json.dumps(data)

            req = requests.put(final_endpoint, headers=self.headers, data=data_json)
            pp.pprint(req.json())
            return req

        print(f"Something went wrong changing {queue_id} \n")
        pp.pprint(req.json())
        return req