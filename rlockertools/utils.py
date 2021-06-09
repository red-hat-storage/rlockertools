import pprint as pp
import json


def prettify_output(text):
    """
    Trying to print the output nicer when it is JSON
    :param text: Text to print
    :return:
    """
    try:
        pp.pprint(json.loads(text.encode("utf8")))
    except:
        print(text)
