import sys,re,os
from argparse import ArgumentParser
import wgs84_ch1903
from urllib import parse

parser=ArgumentParser()
parser.add_argument('--outFile','--outF','-o',default='')
parser.add_argument('--snowshoe','-s',action='store_true',default=False)
parser.add_argument('--avgMarker',action='store_true',default=False)
parser.add_argument('--noTrack','-t',action='store_true',default=False)
parser.add_argument('inFiles',nargs='+')

options=parser.parse_args()

if not options.inFiles:
    sys.exit(0)

lineWidth = 3
lineColor = "EEFF4444" # <- color order is aabbggrr
dotURL="https://api3.geo.admin.ch/color/255,0,0/marker-24@2x.png"
if options.snowshoe:    
  lineColor = "CCFF3333" # <- color order is aabbggrr
  dotURL="https://api3.geo.admin.ch/color/255,0,0/marker-24@2x.png"

from xml.etree import cElementTree as ET
def doFile(name,options,idx,includeMarker=False):
    inF = open(name,'r')
    et = ET.ElementTree(file=inF)
    nms = et.findall('.//{http://www.topografix.com/GPX/1/1}name')
    if nms:
        name = nms[0].text

    pts = et.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not pts:
        pts = et.findall('.//{http://www.topografix.com/GPX/1/0}trkpt')
        if not pts:
            raise ValueError('could not find any points')
    data=[]
    for pt in pts:
        data.append((float(pt.get('lat')),float(pt.get('lon'))))

    description = name

    ldotURL = dotURL
    llineColor = lineColor
    markTemplate="""
    <Placemark>
        <name></name>
        <description></description>
      <Style>
        <IconStyle>
          <Icon>
            <href>%(ldotURL)s</href>
            <gx:w>48</gx:w><gx:h>48</gx:h>
          </Icon>
          <hotSpot x="24" y="24" xunits="pixels" yunits="pixels"/>
        </IconStyle>
        <LabelStyle>
          <color>%(llineColor)s</color>
        </LabelStyle>
      </Style>

        <Point>
          <coordinates>%(markerX)f,%(markerY)f</coordinates>
        </Point>
    </Placemark>
    """
    trackTemplate="""
    <Placemark>
        <name>%(name)s-track</name>
        <description>%(description)s-track</description>
        <styleUrl>#trackColor%(idx)d</styleUrl>
        %(lineString)s
    </Placemark>
    """
    txtPairs=["%.6f,%.6f"%(pt[1],pt[0]) for pt in data]
    center=[0.,0.]
    for pt in data:
        lat = pt[0]
        long = pt[1]
        center[0] += lat
        center[1] += long
    center[0] /= len(data)
    center[1] /= len(data)
    lat,long=center
    if options.avgMarker:
        markerX = long
        markerY = lat
    else:
        markerX = data[0][1]
        markerY = data[0][0]
    coords = '\n'.join(txtPairs)
    if not options.noTrack:
        lineString="""
        <LineString>
          <coordinates>
            %(coords)s
          </coordinates>
        </LineString>"""%locals()
    else:
        lineString=""
    track = trackTemplate%locals()
    if includeMarker:
        track += markTemplate%locals()
    return track,center

procData = [doFile(arg,options,idx+1,idx) for (idx,arg) in enumerate(options.inFiles)]
tracks,centers = zip(*procData)
tracks = '\n'.join(tracks)

if options.outFile=='-':
    outF = sys.stdout
else:
    if options.outFile:
        outF = open(options.outFile,'w+')
    else:
        fName = os.path.splitext(options.inFiles[0])[0]+'.kml'
        outF = open(os.path.join('/landrumd/www/kml/',fName),'w+')

styles=[]
for idx in range(1,len(options.inFiles)+1):
    styles.append("""<Style id="trackColor%(idx)d">
      <LineStyle>
        <color>%(lineColor)s</color>
        <width>%(lineWidth)s</width>
      </LineStyle>
    </Style>"""%globals())
styles = '\n'.join(styles)

template="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/kml/2.2 https://developers.google.com/kml/schema/kml22gx.xsd">
<Document>
    %(styles)s
%(tracks)s
</Document>
</kml>
"""
print(template%locals(),file=outF)

center = [0,0]
for c in centers:
    center[0] += c[0]
    center[1] += c[1]
center[0]/=len(centers)
center[1]/=len(centers)
converter = wgs84_ch1903.GPSConverter()
if not options.outFile:
    y,x,h = converter.WGS84toLV03(center[0],center[1],0)
    qname = parse.quote_plus('http://landrumdecker.com/kml/%s'%fName)
    blog_text="<iframe src='https://map.geo.admin.ch/embed.html?topic=ech&lang=en&bgLayer=ch.swisstopo.pixelkarte-farbe&X={0:.2f}&Y={1:.2f}&zoom=4&layers=KML%7C%7C{2}' width='100%' height='300' frameborder='0' style='border:0'></iframe>".format(x,y,qname)
    print(blog_text)
