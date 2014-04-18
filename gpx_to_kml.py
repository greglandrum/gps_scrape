import sys,re,os
from optparse import OptionParser

parser=OptionParser()
parser.add_option('--outFile','--outF','-o',default='')
parser.add_option('--snowshoe','-s',action='store_true',default=False)
parser.add_option('--avgMarker',action='store_true',default=False)
parser.add_option('--noTrack','-t',action='store_true',default=False)

options,args =parser.parse_args()

if not args:
    sys.exit(0)

lineWidth = 3
lineColor = "EE00AA00" # <- color order is aabbggrr
dotURL="http://www.google.com/intl/en_us/mapfiles/ms/icons/green-dot.png"
if options.snowshoe:    
  lineColor = "CCFF3333" # <- color order is aabbggrr
  dotURL="http://www.google.com/intl/en_us/mapfiles/ms/icons/blue-dot.png"

from xml.etree import cElementTree as ET
def doFile(name,options,idx):
    inF = file(name,'ru')
    et = ET.ElementTree(file=inF)
    nms = et.findall('.//{http://www.topografix.com/GPX/1/1}name')
    if nms:
        name = nms[0].text

    pts = et.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not pts:
        pts = et.findall('.//{http://www.topografix.com/GPX/1/0}trkpt')
        if not pts:
            raise ValueError,'could not find any points'
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
    lat,long=center
    lat /= len(data)
    long /= len(data)
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
    return track

tracks = [doFile(arg,options,idx+1) for (idx,arg) in enumerate(args)]
tracks = '\n'.join(tracks)
    
if options.outFile=='-':
    outF = sys.stdout
else:
    if options.outFile:
        outF = file(options.outFile,'w+')
    else:
        fName = os.path.splitext(args[0])[0]+'.kml'
        outF = file(fName,'w+')

styles=["""<Style id="trackColor%(idx)d">
      <LineStyle>
        <color>%(lineColor)s</color>
        <width>%(lineWidth)s</width>
      </LineStyle>
        <IconStyle> 
          <Icon> 
            <href>%(dotURL)s</href> 
          </Icon> 
        </IconStyle> 
    </Style>"""%locals() for idx in range(1,len(args)+1)]
styles = '\n'.join(styles)

template="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    %(styles)s
%(tracks)s
</Document>
</kml>
"""
print >>outF,template%locals()
