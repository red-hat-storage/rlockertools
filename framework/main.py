import os
import signal
import pprint as pp
from urllib.parse import quote
from argparse import ArgumentParser
from rlockertools.resourcelocker import ResourceLocker
import sys

def init_argparser():
    """
    Initialization  of argument parse library with it's arguments
    Args:
        None

    Returns:
        object: Parsed arguments - returned from parser.parse_args()
    """

    parser = ArgumentParser()
    parser.add_argument(
        "--server-url",
        help="The URL of the Resource Locker Server",
        required=True,
        action="store",
    )
    parser.add_argument(
        "--token",
        help="Token of the user that creates API calls",
        required=True,
        action="store",
    )
    parser.add_argument(
        "--release", help="Use this argument to release a resource", action="store_true"
    )
    parser.add_argument(
        "--lock", help="Use this argument to lock a resource", action="store_true"
    )
    parser.add_argument(
        "--signoff",
        help="Use this when lock=True, locking a resource requires signoff",
        action="store",
    )
    parser.add_argument(
        "--priority",
        help="Use this when lock=True, specify the level of priority the resource should be locked",
        action="store",
    )
    parser.add_argument(
        "--search-string",
        help="Use this when lock=True, specify the lable or the name of the lockable resource",
        action="store",
    )
    parser.add_argument(
        "--link",
        help="Use this when lock=True, specify the link of the CI/CD pipeline that locks the resource",
        action="store",
    )
    parser.add_argument(
        "--interval",
        help="Use this when lock=True, how many seconds to wait between each call"
             " while checking for a free resource",
        type=int,
        action="store",
    )
    parser.add_argument(
        "--attempts",
        help="Use this when lock=True, how many times to create an API call"
             " that will check for a free resource ",
        type=int,
        action="store",
    )
    return parser.parse_args()


def run(args):
    """

    Function of the actions against the Resource Locker endpoint
    Args:
        args (object): Parsed arguments - returned from parser.parse_args()

    Returns:
        None
    """

    # Instantiate the connection vs Resource locker:
    inst = ResourceLocker(instance_url=args.server_url, token=args.token)
    if args.release:
        resource_to_release = inst.get_lockable_resources(
            signoff=args.signoff
        )[0]
        if resource_to_release:
            release_attempt = inst.release(resource_to_release)
            print(release_attempt.text)

    if args.lock:
        new_queue = inst.find_resource(
            search_string=args.search_string,
            signoff=args.signoff,
            priority=int(args.priority),
            link=quote(args.link, safe="") if args.link else None,
        )
        # We should verify that the resource has been locked by checking
        # if the queue is finished.
        # timeout is -> attempts * interval

        abort_action = inst.abort_queue
        abort_action_args = {
            "queue_id"  : new_queue.json().get('id'),
            "abort_msg" : "Queue has been aborted in the middle of a CI/CD Pipeline \n"
                          "or during manual execution."
        }

        def signal_handler(sig, frame):
            abort_action(**abort_action_args)
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGBREAK, signal_handler)

        verify_lock = inst.wait_until_finished(
            queue_id=new_queue.json().get('id'),
            interval=args.interval,
            attempts=args.attempts,
            silent=False,
            abort_on_timeout=True
        )
        # If it will return any object, it means the condition is achieved:
        if verify_lock:
            print('Resource Locked Successfully! Info: \n')
            # We print json response, it is better to visualize it nicer:
            pp.pprint(verify_lock)


def main():
    os.environ['PYTHONUNBUFFERED'] = '1'
    args = init_argparser()
    run(args)
