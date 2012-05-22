#! /usr/bin/python
# wget -O shapes.json "http://api.talis.com/stores/ordnance-survey/services/sparql?output=json&query=select+%3Fs+%3Fg+where+{%3Fs+<http%3A%2F%2Fdata.ordnancesurvey.co.uk%2Fontology%2Fgeometry%2Fextent>+%3Fe+.%0D%0A%3Fe+<http%3A%2F%2Fdata.ordnancesurvey.co.uk%2Fontology%2Fgeometry%2FasGML>+%3Fg+.%0D%0A%0D%0A}"

import shapefile
from geohelpers import *
import sys
import os
from os.path import isfile, exists, isdir
from shapely.geometry import Polygon
import re
from xml.etree import ElementTree


class BoundaryConverter:

  def convert(self, filename, outfilename):
    fout = open(outfilename, 'w')

    f = open(filename, 'r')
    subject = None

    count = 0

    for line in f:
      if not subject:
        m = re.search(r"""\s+"s".+value": "(.+?)" """, line)
        if m:
          subject = m.group(1)
          
      else:
        m = re.search(r"""\s+"g".+value": "(.+?)" }""", line)
        if m:
          gmldata = m.group(1).replace("\\\"", "\"").replace("\\/", "/")
          shape =  self.read_polygon(gmldata)
          if shape:
            fout.write("%s\t%s\n" % (subject, shape.wkt))

            count += 1
            if count > 0:
              if count % 1000 == 0:
                print str(count) + " shapefiles processed"
                sys.stdout.flush()
              elif count % 25 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

          subject = None


    
    print str(count) + " shapefiles processed"
    f.close()
    fout.close()

  def read_polygon(self, string):
    element = ElementTree.fromstring(string)
    outer = element.find('{%s}exterior' % "http://www.opengis.net/gml")
    if outer:
      text = outer.findtext('*/{%s}posList' % "http://www.opengis.net/gml")
      if text:
        _re_space = re.compile(r'\s+')
        coords = _re_space.sub(' ', text).strip().split()
        plist = []
        for i in range(0, len(coords), 2):
          (lat, lng) = turn_eastingnorthing_into_latlong(float(coords[i]), float(coords[i+1]), 'osgb')
          (lat, lng, height) = turn_osgb36_into_wgs84(lat, lng, 0)
          plist.append((float(lng), float(lat)))
        return Polygon(tuple(plist),)

    return None

  
if __name__ == "__main__":
  conv = BoundaryConverter()
  conv.convert('/home/iand/data/datasets/ordnancesurvey/shapes.json','/home/iand/wip/os-boundaries/os.dat')
