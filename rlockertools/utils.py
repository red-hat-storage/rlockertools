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

def parse_queue_data(data_section):
    """
    Somehow a workaround for the data section (JSON Field) in Django.
    In some cases, Django loads the field as str and in some dictionary.
    Hence, check the data section's type and return dict, always
    :param data_section:
    :return dict:
    """
    return json.loads(data_section) if isinstance(data_section, str) else data_section
