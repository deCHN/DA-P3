# -*- coding: utf-8 -*-
'''
Project DA-P3 data wrangling.
This script takes an open street map in xml format, processes auditing, cleaning and shaping, to generate a json document.

Merged from:
- audit.py
- prepareDB.py

Code auto-format and convention:
    `autopep8 -ai --max-line-length 200'
'''
import sys
import codecs
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import cerberus
import schema
import json

''' Input file to be audit, cleaned and shaped into json doc '''
OSMFILE = "./munich_germany_k10.osm"

SCHEMA = schema.schema

'''
For all these suffix, auditing accepts the street name in form of:
    abcstraße
    abc-straße
    abc straße
'''
street_type_re = re.compile(
    ur'(\s|-)?(straße|weg|ring|platz|allee|bogen|gasse|brücke|hof|berg|eck)$',
    re.IGNORECASE | re.UNICODE)

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')

problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

''' A street name which contains any of the string in this list will pass the audit.
e.g.:
    Am Krautgarten
    Im Wismat
    Zu Maria-Eich
    Zur Allacher
'''
expected = ["am", "an", "im", "in", "zu", "bach", "insel", "kreppe", "park", "hof", "winkel", "garten", "wiese", "wald", "markt", "feld"]

''' The unexpected street types to the appropriate ones in the expected list.  The variable 'mapping' to reflect the changes needed to fix. '''
mapping = {u"St": u"Street", u"Str.": u"Straße", u"Ave": u"Avenue", u"Rd.": u"Road", u"St.": u"Street"}

# structure these attributes into 'created' document
CREATED = ["version", "changeset", "timestamp", "user", "uid"]


def routine(osmfile, validate=False, pretty=False):
    ''' osm data goes throw a routine for auditing, shaping, validation and final results will be stored in a json file.
    Args:
        osmfile str - osm input file
        validate bool - validate the element against a schema
        pretty bool - line break and indent for output file
    Return:
        unexpeceted (none match) street names in a dictionary.
    '''
    osm_file = codecs.open(osmfile, "r", "utf-8")
    street_types = defaultdict(set)

    file_out = "{0}.json".format(osmfile)
    data = []
    validator = cerberus.Validator()

    with codecs.open(file_out, "w", "utf-8") as fo:
        for event, elem in ET.iterparse(osm_file, events=("start",)):
            if elem.tag == "node" or elem.tag == "way":
                # Audit element
                audit(elem, street_types)

                # Shape element
                el = shape(elem)
                if el:
                    # Validate element
                    if validate is True:
                        validate_element(el, validator)
                    data.append(el)

                    # Persist element
                    if pretty:
                        fo.write(json.dumps(el, indent=2, ensure_ascii=False).encode('utf-8') + "\n")
                    else:
                        fo.write(json.dumps(el) + "\n")

    osm_file.close()
    return street_types


def audit(elem, street_types):
    ''' Audit the street name in tag's value of "node" or "way" element, which in a format like "addr:street".
    Args:
        elem str - input xml element
    '''
    for tag in elem.iter("tag"):
        if is_street_name(tag):
            audit_street_type(street_types, tag.attrib['v'])
        if is_country_name(tag):
            # All data wihin this area should have county name "DE"
            audit_country_name(tag)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def is_country_name(elem):
    return (elem.attrib['k'] == "addr:country")


def audit_street_type(street_types, street_name):
    ''' First the (over abbreviated) street name would be updated after the mapping dictionary.
        Second, check the street name against an expected pattern. Add unexpected name(none pattern match) into a dictionary for further investigation.
    Args:
        steet_type - collections.defaultdict
        street_name - string

    '''
    update_name(street_name, mapping)
    m = street_type_re.search(street_name)
    if m is None and isNotExpected(street_name):
        street_types[street_name.rsplit(' ', 1)[-1]].add(street_name)


def update_name(name, mapping):
    ''' The function takes a string with street name as an argument and should return the fixed name.
    Args:
        name str - street name to fix
        mapping {str: str} - dict of name mapping
    '''
    str_type = name.rsplit(' ', 1)
    if len(str_type) == 2 and str_type[1] in mapping:
        name = str_type[0] + ' ' + mapping[str_type[1]]


def audit_country_name(tag):
    tag.attrib['v'] = "DE"


def shape(element):
    ''' Shape the xml element into a json object.
    Args:
        element xml.etree.cElementTree<event, elem> - xml element.
    Return:
        shaped element.

    This function transforms the shape of the data into the model which look like this:
    {
        "id": "2406124091",
        "type: "node",
        "visible":"true",
        "created": {
            "version":"2",
            "changeset":"17206049",
            "timestamp":"2013-08-03T16:43:42Z",
            "user":"linuxUser16",
            "uid":"1219059"
            },
        "pos": [41.9757030, -87.6921867],
        "address": {
            "housenumber": "5157",
            "postcode": "60625",
            "street": "North Lincoln Ave"
            },
        "amenity": "restaurant",
        "cuisine": "mexican",
        "name": "La Cabana De Don Luis",
        "phone": "1 (773)-271-5176"
    }

    In particular the following things have done:
    - you should process only 2 types of top level tags: "node" and "way"
    - all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array, for use in geospacial indexing. Make sure the values inside "pos" array are floats and not strings.
    - if the second level tag "k" value contains problematic characters, it should be ignored
    - if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
    - if the second level tag "k" value does not start with "addr:", but contains ":", you can process it in a way that you feel is best. For example, you might split it into a two-level dictionary like with "addr:", or otherwise convert the ":" to create a valid key.
    - if there is a second ":" that separates the type/direction of a street, the tag should be ignored, for example:
    <tag k="addr:housenumber" v="5158"/>
    <tag k="addr:street" v="North Lincoln Avenue"/>
    <tag k="addr:street:name" v="Lincoln"/>
    <tag k="addr:street:prefix" v="North"/>
    <tag k="addr:street:type" v="Avenue"/>
    <tag k="amenity" v="pharmacy"/>

    should be turned into:
    {   ...
        "address": {
            "housenumber": 5158,
            "street": "North Lincoln Avenue"
            }
        "amenity": "pharmacy",
        ...
    }

    - for "way" specifically:

    <nd ref="305896090"/>
    <nd ref="1719825889"/>

    should be turned into:

    "node_refs": ["305896090", "1719825889"]
    '''
    node = {}

    node['type'] = element.tag

    created = {}
    pos = [0.0] * 2
    for attr in element.attrib:
        if attr in CREATED:
            created[attr] = element.attrib.get(attr)
        elif attr == "lat":
            pos[0] = float(element.attrib.get(attr))
        elif attr == "lon":
            pos[1] = float(element.attrib.get(attr))
        else:
            node[attr] = element.attrib.get(attr)
    node['created'] = created
    node['pos'] = pos

    address = {}
    for tag in element.iter('tag'):
        key = tag.attrib.get('k')
        value = tag.attrib.get('v')

        # put address related infomation in one dictionary
        addrs = key.split('addr:')
        if len(addrs) == 2:
            if ':' not in addrs[1]:
                address[addrs[1]] = value
        if bool(address):
            node['address'] = address
        # As tag's '<k>-value' may contain 'dot', which would cause problem, here I simply drop those tags.
        # as fieldname in mongodb,
        elif '.' not in key:
            node[key] = value

    if element.tag == "way":
        ndRef = []
        for nd in element.iter('nd'):
            ndRef.append(nd.attrib.get('ref'))
        node['node_refs'] = ndRef

    return node


def isNotExpected(streetName):
    for e in expected:
        if e.lower() in streetName.lower():
            return False
    return True


def validate_element(element, validator, schema=SCHEMA):
    ''' Raise ValidationError if element does not match schema. '''
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


def test():
    unexpected_st_types = routine(OSMFILE)
    pprint.pprint(dict(unexpected_st_types))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    test()
