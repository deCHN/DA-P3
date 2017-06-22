#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
In this problem set you work with another type of infobox data, audit it, clean it,
come up with a data model, insert it into a MongoDB and then run some queries against your database.
The set contains data about Arachnid class.
Your task in this exercise is to parse the file, process only the fields that are listed in the
FIELDS dictionary as keys, and return a dictionary of cleaned values.

The following things should be done:
- keys of the dictionary changed according to the mapping in FIELDS dictionary
- trim out redundant description in parenthesis from the 'rdf-schema#label' field, like "(spider)"
- if 'name' is "NULL" or contains non-alphanumeric characters, set it to the same value as 'label'.
- if a value of a field is "NULL", convert it to None
- if there is a value in 'synonym', it should be converted to an array (list)
  by stripping the "{}" characters and splitting the string on "|". Rest of the cleanup is up to you,
  eg removing "*" prefixes etc
- strip leading and ending whitespace from all fields, if there is any
- the output structure should be as follows:
{ 'label': 'Argiope',
  'uri': 'http://dbpedia.org/resource/Argiope_(spider)',
  'description': 'The genus Argiope includes rather large and spectacular spiders that often ...',
  'name': 'Argiope',
  'synonym': ["One", "Two"],
  'classification': {
                    'family': 'Orb-weaver spider',
                    'class': 'Arachnid',
                    'phylum': 'Arthropod',
                    'order': 'Spider',
                    'kingdom': 'Animal',
                    'genus': None
                    }
}
"""
import codecs
import csv
import json
import pprint
import re


DATAFILE = 'arachnid.csv'

FIELDS = {'rdf-schema#label': 'label',
          'URI': 'uri',
          'rdf-schema#comment': 'description',
          'synonym': 'synonym',
          'name': 'name',
          'family_label': 'family',
          'class_label': 'class',
          'phylum_label': 'phylum',
          'order_label': 'order',
          'kingdom_label': 'kingdom',
          'genus_label': 'genus'
          }


def lableRule(v):
    # trim out redundant description in parenthesis from the
    # 'rdf-schema#label' field, like "(spider)"
    p = v.find("(")
    if p != -1:
        v = v[:(p - 1)]

    return v


def addToClass(v):
    return v


def synonymRule(v):
    # if there is a value in 'synonym', it should be converted to an array
    # (list) by stripping the "{}" characters and splitting the string on "|".
    # Rest of the cleanup is up to you, eg removing "*" prefixes etc
    if v is not None:
        return parse_array(v)
    return v


def nameRule(v):
    # if 'name' is "NULL" or contains non-alphanumeric characters, set it to
    # the same value as 'label'.
    if not isinstance(v, type('str')):
        return None
    return v


def noRule(v):
    return v


CLASSES = ['family', 'class', 'phylum', 'order', 'kingdom', 'genus']

rulz = {
    k: addToClass for k in CLASSES
}

rulz['label'] = lableRule
rulz['name'] = nameRule
rulz['synonym'] = synonymRule
rulz['description'] = noRule
rulz['uri'] = noRule


def process_file(filename, fields):
    process_fields = fields.keys()
    data = []

    with open(filename, "r") as f:
        reader = csv.DictReader(f)

        for i in range(3):
            l = reader.next()

        for line in reader:
            # YOUR CODE HERE
            entry = {}
            classification = {}
            for field in line:
                if field in process_fields:
                    fieldname = FIELDS[field]

                    # strip leading and ending whitespace from all fields
                    fieldvalue = line[field].strip('\t\n\r')

                    # "NULL" to None
                    fieldvalue = nullToNone(fieldvalue)

                    # Overkill...
                    entry[fieldname] = rulz[fieldname](fieldvalue)

            for e in CLASSES:
                classification[e] = entry.pop(e)

            if entry['name'] is None:
                entry['name'] = entry['label']

            entry["classification"] = classification
            data.append(entry)
    return data


def nullToNone(v):
    if v == "NULL":
        return None
    else:
        return v


def parse_array(v):
    if (v[0] == "{") and (v[-1] == "}"):
        v = v.lstrip("{")
        v = v.rstrip("}")
        v_array = v.split("|")
        v_array = [i.strip() for i in v_array]
        return v_array
    return [v]


def test():
    data = process_file(DATAFILE, FIELDS)

    pprint.pprint(data[0])
    assert data[0] == {
        "synonym": None,
        "name": "Argiope",
        "classification": {
                "kingdom": "Animal",
                "family": "Orb-weaver spider",
                "order": "Spider",
                "phylum": "Arthropod",
                "genus": None,
                "class": "Arachnid"
        },
        "uri": "http://dbpedia.org/resource/Argiope_(spider)",
        "label": "Argiope",
        "description": "The genus Argiope includes rather large and spectacular spiders that often have a strikingly coloured abdomen. These spiders are distributed throughout the world. Most countries in tropical or temperate climates host one or more species that are similar in appearance. The etymology of the name is from a Greek name meaning silver-faced."
    }


if __name__ == "__main__":
    test()
