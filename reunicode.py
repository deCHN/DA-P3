# coding=utf-8
import re
import sys
import xml.etree.cElementTree as ET
import codecs

street_type_re = re.compile(
    ur'(\s|-)?(straße|weg|ring|platz|allee)$',
    re.IGNORECASE | re.UNICODE)

# x - street_type_re = re.compile(
# ur'-


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def test():
    osm_file = codecs.open(
        './munich_germany_k10.osm',
        mode='r',
        encoding='utf-8')

    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    s = tag.attrib['v']
                    # s = "aaastraße"
                    m = street_type_re.search(s)
                    if m is None:
                        print s
                    else:
                        print '<string: %r, start=%r, end=%r, match=%r>' % (m.string, m.start(), m.end(), m.group())


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    test()
