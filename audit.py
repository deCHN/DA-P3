# -*- coding: utf-8 -*-
import sys
import codecs
"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix
the unexpected street types to the appropriate ones in the expected list.
You have to add mappings only for the actual problems you find in this OSMFILE,
not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
The function takes a string with street name as an argument and should return the fixed name
We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "./munich_germany_k10.osm"

street_type_re = re.compile(
    ur'(\s|-)?(straße|weg|ring|platz|allee|bogen|gasse|brücke|hof|berg|eck)$',
    re.IGNORECASE | re.UNICODE)

expected = [
    "am",
    "an",
    "im",
    "in",
    "zu",
    "bach",
    "insel",
    "kreppe",
    "park",
    "hof",
    "winkel",
    "garten",
    "wiese",
    "wald",
    "markt",
    "feld"]

# UPDATE THIS VARIABLE
mapping = {
    "St": "Street",
    "Str.": "Straße",
    "Ave": "Avenue",
    "Rd.": "Road",
    "St.": "Street"}


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m is None and isNotExpected(street_name):
        street_types[street_name.rsplit(' ', 1)[-1]].add(street_name)


def isNotExpected(streetName):
    for e in expected:
        if e.lower() in streetName.lower():
            return False
    return True


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = codecs.open(osmfile, "r", "utf-8")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

    osm_file.close()
    return street_types


def update_name(name, mapping):
    # YOUR CODE HERE
    str_type = name.rsplit(' ', 1)
    if len(str_type) != 2:
        return name
    else:
        return str_type[0] + ' ' + mapping[str_type[1]]


def test():
    st_types = audit(OSMFILE)
    pprint.pprint(dict(st_types))

    # for st_type, ways in st_types.iteritems():
    # for name in ways:
    # better_name = update_name(name, mapping)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    test()
