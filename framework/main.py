import json
import os
import signal
import pprint as pp
import time
from urllib.parse import quote
from requests.exceptions import ConnectionError
from argparse import ArgumentParser
from rlockertools.resourcelocker import ResourceLocker
import sys


def init_argparser(args=None):
    """
    Initialization  of argument parse library with it's arguments
    Args:
        args: list of args to parse in `sys.argv` form. Useful for testing
            passed to `ArgumentParser.parse_args` . default to None (use `sys.argv`)

    Returns:
        object: Parsed arguments - returned from parser.parse_args()
    """
    server_args_parser = ArgumentParser(add_help=False)

    # sharing arguments using parent parsers.
    # https://stackoverflow.com/a/56595689 and https://stackoverflow.com/a/7498853

    # TODO These really should be config file things,
    server_args_parser.add_argument(
        "-s",
        "--server-url",
        help="The URL of the Resource Locker Server",
        required=True,
        action="store",
    )
    server_args_parser.add_argument(
        "-t",
        "--token",
        help="Token of the user that creates API calls",
        required=True,
        action="store",
    )
    server_args_parser.add_argument(
        "--resume-on-connection-error",
        help="Use this argument in case you don't want to break queue execution"
        " in the middle of waiting for queue status being FINISHED",
        action="store_true",
    )

    # TODO Come up with a better way of handling defaults in ResourceLocker
    # Doing interval here since it is required as part of `--resume-on-connection-error`
    interval_default = 15
    server_args_parser.add_argument(
        "-i",
        "--interval",
        help=f"How many seconds to wait between each call (default {interval_default})",
        type=int,
        action="store",
        default=interval_default,
    )

    parser = ArgumentParser(parents=[server_args_parser])

    # Parent of all sub commands that take a search string
    search_parser = ArgumentParser(add_help=False)
    search_parser.add_argument(
        "search_string",
        metavar="SEARCH",
        help="Specify the label or the name of the lockable resource",
    )

    # Parent of all sub commands that take a signoff string
    signoff_parser = ArgumentParser(add_help=False)
    signoff_parser.add_argument(
        "signoff",
        metavar="SIGN_OFF",
        help="locking or releasing a resource requires signoff",
    )

    # subcommands
    subparsers = parser.add_subparsers(dest="action")

    # release
    release_parser = subparsers.add_parser(
        "release",
        # parents=[server_args_parser, signoff_parser],
        parents=[signoff_parser],
        help="Release a resource",
    )

    # check
    check_parser = subparsers.add_parser(
        "check",
        # parents = [server_args_parser, search_parser],
        parents=[search_parser],
        help="check a resource",
    )

    # lock
    lock_parser = subparsers.add_parser(
        "lock",
        parents=[search_parser, signoff_parser],
        help="Lock a resource",
    )
    lock_parser.add_argument(
        "priority",
        help="Specify the level of priority the resource should be locked",
        metavar="PRIORITY",
    )
    # TODO Come up with a better way of handling defaults in ResourceLocker class
    attempts_default = 120
    lock_parser.add_argument(
        "-a",
        "--attempts",
        help="How many times to create an API call"
        f" that will check for a free resource (default {attempts_default})",
        type=int,
        action="store",
        default=attempts_default,
    )
    lock_parser.add_argument(
        "-l",
        "--link",
        help="Specify the link of the CI/CD pipeline that locks the resource",
        action="store",
    )

    return parser.parse_args(args=args)


def run(args):
    """

    Function of the actions against the Resource Locker endpoint
    Args:
        args (object): Parsed arguments - returned from parser.parse_args()

    Returns:
        None
    """
    try:
        # Instantiate the connection vs Resource locker:
        inst = ResourceLocker(instance_url=args.server_url, token=args.token)
        if args.action == "release":
            resource_to_release = inst.get_lockable_resources(signoff=args.signoff)
            if resource_to_release:
                release_attempt = inst.release(resource_to_release[0])
                print(release_attempt.text)
            else:
                print(f"There is no resource: {args.signoff} locked, ignoring!")

        elif args.action == "lock":
            new_queue = inst.find_resource(
                search_string=args.search_string,
                signoff=args.signoff,
                priority=int(args.priority),
                link=quote(args.link, safe="") if args.link else None,
            )
            # Save the queue id in a file
            with open("queue_id.log", "w") as f:
                f.write(f"{new_queue.json().get('id')}")
            # We should verify that the resource has been locked by checking
            # if the queue is finished.
            # timeout is -> attempts * interval

            abort_action = inst.abort_queue
            abort_action_args = {
                "queue_id": new_queue.json().get("id"),
                "abort_msg": "Queue has been aborted in the middle of a CI/CD Pipeline \n"
                "or during manual execution.",
            }

            def signal_handler(sig, frame):
                abort_action(**abort_action_args)
                sys.exit(0)

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            verify_lock = inst.wait_until_finished(
                queue_id=new_queue.json().get("id"),
                interval=args.interval,
                attempts=args.attempts,
                silent=False,
                abort_on_timeout=True,
                resume_on_connection_error=args.resume_on_connection_error,
            )
            # If it will return any object, it means the condition is achieved:
            if verify_lock:
                print("Resource Locked Successfully! Info: \n")
                # We print json response, it is better to visualize it nicer:
                pp.pprint(verify_lock)

        elif args.action == "check":
            resources_by_name = inst.get_lockable_resources(name=args.search_string)
            resources_by_label = inst.get_lockable_resources(label_matches=args.search_string)
            if (resources_by_name or resources_by_label):
                print("Resources are available:")
                print(f"by name: {json.dumps(resources_by_name)}")
                print(f"by label: {json.dumps(resources_by_label)}")
            else:
                print(f"No resource available.")
                sys.exit(3)

    except (ConnectionError) as e:
        print(
            "Connection Error! \n"
            "Error is: \n"
            f"{str(e)}"
        )
        if args.resume_on_connection_error:
            print(f"You chose to continue on connection errors, will try again in {args.interval} seconds!")
            time.sleep(args.interval)
            run(args)
        else:
            print("You chose to NOT continue on connection errors. \n"
                  "To prevent this, you can run next time with --resume-on-connection-error! \n"
                  "Exiting ... ")
    except Exception as e:
        print("An unexpected error occured!")
        raise


def main():
    os.environ["PYTHONUNBUFFERED"] = "1"
    args = init_argparser()
    run(args)
