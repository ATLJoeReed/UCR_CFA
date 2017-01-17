import re

import dataset
import usaddress

from config import settings, constants


db = dataset.connect(settings.DB_URL)
working_table = db[constants.SOURCE_TABLE_NAME]
parsed_table = db[constants.PARSED_TABLE_NAME]
ga_entities = working_table.find(agency_name='GA')


def un_camel(s):
    """
    Takes in camel cased string and converts it to lower case understore
    string.

    Example: CamelCase --> camel_case

    Args:
    __s__: string to convert

    Returns: converted string
    """
    result = ''
    text = s.replace(' ', '')
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    return result.replace('__', '_').replace(' ', '')


def convert_dict_keys(d):
    """
    Takes in dict and converts the keys to lower case understore
    string. This function utilizes the un_camel function


    Args:
    __d__: dict to convert

    Returns: converted dict
    """
    return {un_camel(k): v for k, v in d.items()}


def fix_address(s):
    """
    Takes in a string and attempts to put a space between the street
    address and PO Box...

    This was needed to deal with the discover policing data that was
    scrape for the Code For Atlanta FBI UCR project.

    Args:
    __s__: string to convert

    Returns: converted string
    """
    if s.find('PO Box') > 0:
        loc = s.find('PO Box')
        fixed_address = s[:loc] + ' ' + s[loc:]
    elif s.find('P.O. Box') > 0:
        loc = s.find('P.O. Box')
        fixed_address = s[:loc] + ' ' + s[loc:]
    elif s.find('P. O. Box') > 0:
        loc = s.find('P.O. Box')
        fixed_address = s[:loc] + ' ' + s[loc:]
    elif s.find('P O Box') > 0:
        loc = s.find('P.O. Box')
        fixed_address = s[:loc] + ' ' + s[loc:]
    else:
        fixed_address = s
    return fixed_address


for org in ga_entities:
    address_to_parse = fix_address(org[constants.ADDRESS_FIELD])
    print(address_to_parse)
    try:
        address_parsed, address_type = usaddress.tag(
            address_to_parse
        )
    except usaddress.RepeatedLabelError as e:
        address_parsed = ''
        address_type = 'Parsing Error'

    data = convert_dict_keys(dict(address_parsed))
    data.update({
        'address_type': address_type,
        'ukey': org['ukey'],
        'input_address': org[constants.ADDRESS_FIELD],
        })
    parsed_table.insert(data)