#! /usr/bin/python
"""
Matches geographic points in a Kasabi dataset to the Ordnance Survey administrative region
that it is in. It uses the OS boundary data to determine whether a given point is in the
region or not.

Usage:

If you don't have os.dat then you need to run parse-boundaries.py first.

This script takes the following parameters:

  -d/--dataset   the dataset containing the geopoints
  -f/--file      the name of the output file
  -q/--query     an alternate sparql query to use

The sparql query must be a select and must select at least three variables
called ?s, ?lat and ?long being the subject, latitude and longitude

The default query is:

select ?s ?lat ?long where {
  ?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat ; 
     <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long . 
}

Prerequisites:

Set an environment variable KASABI_API_KEY equal to your Kasabi api key. On
Linux you can do this by adding this line to your ~/.profile file:

export KASABI_API_KEY=blah

You also need to install ijson which is a python wrapper for the yajl streaming json parser.

ijson: http://pypi.python.org/pypi/ijson/
yajl: http://lloyd.github.com/yajl/


Install ruby and cmake
  
    sudo apt-get install ruby
    sudo apt-get install cmake


Download the version 1 source of yajl (not version 2), unpack and in
the source directory type:

    sudo ./configure
    sudo make install
    sudo ldconfig 
    
Install ijson with:

    sudo easy_install ijson


"""
import sys
import os
import re
import optparse

from shapely.geometry import Polygon, Point
from shapely.wkt import loads
from shapely import iterops
from ijson import items
import urllib2
import urllib
import pytassium


p = optparse.OptionParser()
p.add_option("-d", "--dataset", action="store", dest="dataset", metavar="DATASET", help="use dataset DATASET")
p.add_option("-q", "--query", action="store", dest="query", metavar="QUERY", help="use sparql QUERY")
p.add_option("-f", "--file", action="store", dest="filename", metavar="FILENAME", help="output results to FILENAME")
opts, args = p.parse_args()

if not opts.dataset:
  print "Please supply the name of a kasabi dataset and make sure you're subscribed to its sparql endpoint"
  sys.exit(1)

if not opts.filename:
  print "Please supply the name of the output file"
  sys.exit(1)

if not opts.query:
  query = "select ?s ?lat ?long where {?s <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat ; <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long . }"
else:
  query = opts.sparql

fout = open(opts.filename, "w")

points = []

ds = pytassium.Dataset(opts.dataset, os.environ['KASABI_API_KEY'])
sparql_uri = ds.get_api('sparql').uri

print "Querying dataset for geographic points"

url = "%s?query=%s&apikey=%s" % (sparql_uri, urllib.quote_plus(query), os.environ['KASABI_API_KEY'])
req = urllib2.Request(url, None, {'Accept':'application/json'})
f = urllib2.urlopen(req)
objects = items(f, 'results.bindings.item')
count = 0
for t in objects:
  p = Point(float(t['long']['value']), float(t['lat']['value']))
  p.uri = t['s']['value']
  points.append(p)
  
  count += 1
  if count > 0:
    if count % 1000 == 0:
      print str(count) + " coordinates found"
      sys.stdout.flush()
    elif count % 25 == 0:
      sys.stdout.write('.')
      sys.stdout.flush()

      
print str(count) + " coordinates found"

print "Matching points to regions"


f = open('os.dat', 'r')
count = 0
for line in f:
  (region, wkt) = line.split("\t") 
  polygon = loads(wkt)
  for point in iterops.contains(polygon, points, True):
    fout.write("<%s> <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/within> <%s> .\n" % (point.uri, region))
    fout.write("<%s> <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/contains> <%s> .\n" % (region, point.uri))
    
  count += 1
  if count > 0:
    if count % 1000 == 0:
      print str(count) + " regions checked"
      sys.stdout.flush()
    elif count % 25 == 0:
      sys.stdout.write('.')
      sys.stdout.flush()

print str(count) + " regions checked"
f.close()
fout.close()



