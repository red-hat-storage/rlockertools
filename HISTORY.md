# Change log

## [0.3.8] - 2021-03-15

Initial build

## [0.3.9] - 2021-07-15

Move to new repo + bug fix

## [0.3.10] - 2021-07-15

Fix build issue

## [0.3.11] - 2021-07-19

Suppress the logs
Show safe errors when beating a queue returns !=200 status code

## [0.4] - 2022-04-12

Allow **datakwargs in the change queue method.
This is necessary to allow modification of the data section once a queue is changing

## [0.4.1] - 2022-04-13

Show more output in get_queue method in case of non 200 status code

## [0.4.2] - 2022-04-17

Address item assignment for str, should be fixed to a dictionary in change queue method

## [0.4.3] - 2022-04-28

Adding log file in order to track after the queue id number once executing from the rlock entrypoint.
Reason: In order to to API calls about the queue, we need to save it in some readable location

## [0.4.4] - 2022-06-09

Adding support for `--check` argument which will return if the given `--search-string` has available resources
by label or a name. Commit number: #15

Usage example:
`rlock --check --search-string=aws-east-2 --token=$token --server-url=$SERVER_URL`

## [0.4.5] - 2022-07-26

Fixing JSON parsing for the data section in a queue, which was not fixed totally in 0.4.2

## [0.4.6] - 2026-02-18

Limit the output from rlock when waiting for resource

## [0.4.7] - 2026-04-16

update intervals when waiting for resource, use python logging module instead of direct print

## [0.4.8] - 2026-10-13

**Critical bugfix**: Added HTTP request timeouts to prevent rlock from hanging indefinitely

- Added `default_timeout` parameter (30 seconds) to ResourceLocker class
- All HTTP GET and PUT requests now have proper timeouts configured
- Prevents infinite hangs when server becomes unresponsive or network connection drops
- Enables `--resume-on-connection-error` to work correctly by detecting timeouts
- Fixes issue where rlock processes would hang for days waiting for unresponsive servers
