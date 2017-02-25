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
dotURL="http://www.google.com/intl/en_us/mapfiles/ms/icons/green-dot.png"
if options.snowshoe:    
  lineColor = "CCFF3333" # <- color order is aabbggrr
  dotURL="http://www.google.com/intl/en_us/mapfiles/ms/icons/blue-dot.png"

from xml.etree import cElementTree as ET
def doFile(name,options,idx):
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

    trackTemplate="""
    <Placemark>
        <name>%(name)s</name>
        <description>%(description)s</description>
        <styleUrl>#trackColor%(idx)s</styleUrl>
        <Point>
          <coordinates>%(markerX)f,%(markerY)f</coordinates>
        </Point>
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
    return track,center

procData = [doFile(arg,options,idx+1) for (idx,arg) in enumerate(options.inFiles)]
tracks,centers = zip(*procData)
tracks = '\n'.join(tracks)
converter = wgs84_ch1903.GPSConverter()
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
        <IconStyle> 
          <Icon> 
            <href>%(dotURL)s</href> 
          </Icon> 
        </IconStyle> 
    </Style>"""%globals())
styles = '\n'.join(styles)

template="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    %(styles)s
%(tracks)s
</Document>
</kml>
"""
print(template%locals(),file=outF)
if not options.outFile:
    y,x,h = converter.WGS84toLV03(centers[0][0],centers[0][1],0)
    qname = parse.quote_plus('http://landrumdecker.com/kml/%s'%fName)
    blog_text="<iframe src='https://map.geo.admin.ch/embed.html?topic=ech&lang=en&bgLayer=ch.swisstopo.pixelkarte-farbe&X={0:.2f}&Y={1:.2f}&zoom=4&layers=KML%7C%7C{2}' width='100%' height='300' frameborder='0' style='border:0'></iframe>".format(x,y,qname)
    print(blog_text)
