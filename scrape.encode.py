""" Copyright (C) 2009-2014 Greg Landrum


Need something like this at the top of the page:
#-------------
<script src='http://www.google.com/jsapi?key=AIzaSyAltYAof0Tum7c4Te_OufSfPBKMeTNpcfw' type='text/javascript'/>
    <script type='text/javascript'>
    //<![CDATA[

      google.load("maps", "2");
      google.load('visualization', '1',{'packages':['corechart']});

      function drawVisualizations() {
        var divs = document.getElementsByTagName('div');
        for(var i=0;i<divs.length;i++){
          var div = divs[i];
          if( div.className.search('gpsplt')!=-1){
            var idx = div.className.split('_')[1];
            var dtbl = eval('dtbl_'+idx);
            drawVisualization(dtbl,div);
          }
        }
      }
      function drawVisualization(dT,div) {
        chart=new google.visualization.ComboChart(div);
        options={seriesType:'line',
                 series:{2:{type:'scatter'},3:{type:'scatter'}},
                 vAxis:{title:'Height (m)'},
                 hAxis:{title:'Distance (km)'},
                 legend:{position:'none'}
                };
        chart.draw(dT,options);
      }

      function initFunc() {
        var divs = document.getElementsByTagName('div');
        for(var i=0;i<divs.length;i++){
          var div = divs[i];
          if( div.className.search('gpsmap')!=-1){
            var idx = div.className.split('_')[1];
            var mapCenter = eval('mapCenter_'+idx);
            var mapZoom = 11;
            if(eval('typeof(zoom_'+idx+')')!='undefined') mapZoom=eval('zoom_'+idx);
            var map = new google.maps.Map2(div);
            map.addControl(new google.maps.HierarchicalMapTypeControl());
            map.addMapType(G_PHYSICAL_MAP);
            map.addControl(new google.maps.SmallMapControl());
            map.addControl(new google.maps.ScaleControl());
            map.setCenter(mapCenter, mapZoom, G_PHYSICAL_MAP);
            var polyline=0;
            if(eval('typeof(polyline_'+idx+')')!='undefined') polyline=eval('polyline_'+idx);
            if(polyline){
              map.addOverlay(polyline);
            } else{
              var j=0;
              while(1){
                if(eval('typeof(polyline_'+idx+'_'+j+')')!='undefined'){
                  polyline=eval('polyline_'+idx+'_'+j);
                } else {javascript:;
                  polyline=0;
                }
                if(!polyline){
                  break;
                } else {
                  map.addOverlay(polyline);
                }
                j++;
              }
            }
          }
        }
        drawVisualizations()
      }
      google.setOnLoadCallback(initFunc);
    //]]>
    </script>
    //]]>
    </script>
#-------------



"""
import random,cPickle,urllib,zlib,base64
idx = random.randint(1,10000000)
import glineenc
import sys,re,os

lineColor = "#3333FF"
lineOpacity = .8
lineWidth = 2
zoom=11
mapWidth=400
mapHeight=400

if len(sys.argv)==3 and sys.argv[2]!='-' and os.path.splitext(sys.argv[2])[-1]!='.gpx':
    outF = file(sys.argv[2],'w+')
    inNames = [sys.argv[1]]
else:
    outF = sys.stderr
    inNames = sys.argv[1:]

fullPage=False

if fullPage:    
    template="""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <title>Andrea's Photoalbum</title>
    <script src="http://www.google.com/jsapi?key=ABQIAAAA-2_6nxv3s-pbeQzc-voYbBSslllT-6jKSoB3IsditEijrmLKghSHFCu4KsAz3bQiG2RQ1zLa5nMXrg"
      type="text/javascript">
    </script>

    <script type="text/javascript">
    //<![CDATA[
      google.load("maps", "2");
      function initFunc() {
        var divs = document.getElementsByTagName('div');
        for(var i=0;i<divs.length;i++){
          var div = divs[i];
          if( div.className.search('gpsmap')==0){
            var idx = div.className.split('_')[1];
            var mapCenter = eval('mapCenter_'+idx);
            var polyline = eval('polyline_'+idx);
            var mapZoom = 11;
            if(eval('typeof(zoom_'+idx+')')!='undefined') mapZoom=eval('zoom_'+idx);
            if(!mapZoom) mapZoom=11;
            var map = new google.maps.Map2(div);
            map.addControl(new google.maps.HierarchicalMapTypeControl());
            map.addMapType(G_PHYSICAL_MAP);
            map.addControl(new google.maps.SmallMapControl());
            map.addControl(new google.maps.ScaleControl());
            map.setCenter(mapCenter, mapZoom, G_PHYSICAL_MAP);
            map.addOverlay(polyline);
          }
        }
      }
      google.setOnLoadCallback(initFunc);
    //]]>
    </script>
  </head>
  <body onunload="google.maps.Unload()" bgcolor="#999999"  text="#101010" link="#333333" vlink="#dddddd">
<p>foo</p>
<hr />
 <script type="text/javascript"> /*<![CDATA[ */ var mapCenter_%(idx)d=new google.maps.LatLng(%(latit)f,%(longit)f); var polyline_%(idx)d=new google.maps.Polyline.fromEncoded({opacity:"%(lineOpacity).1f",color:"%(lineColor)s",weight:%(lineWidth)d,points:"%(encoding)s",levels:"%(levels)s",zoomFactor:32,numLevels:4}); /* ]]>*/ </script>
<div align='center' class="gpsmap_%(idx)d" style="width: %(mapWidth)dpx; height: %(mapHeight)dpx"></div>
<hr />
<p>bar</p>

</body>
</html>
"""
else:
    template="""
 <script type="text/javascript"> /*<![CDATA[ */ var mapCenter_%(idx)d=new google.maps.LatLng(%(latit)f,%(longit)f); %(pointsText)s /* ]]>*/ </script>
<div align='center' class="gpsmap_%(idx)d" style="width: %(mapWidth)dpx; height: %(mapHeight)dpx"></div>
"""

from xml.etree import cElementTree as ET
data=[]
for inF in inNames:
    line=[]
    inF = file(inF,'ru')
    et = ET.ElementTree(file=inF)
    pts = et.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not pts:
        pts = et.findall('.//{http://www.topografix.com/GPX/1/0}trkpt')
        if not pts:
            pts = et.findall('.//{http://www.topografix.com/GPX/1/0}rtept')
            if not pts:
                raise ValueError,'could not find any points'
    for pt in pts:
        line.append((float(pt.get('lat')),float(pt.get('lon'))))
    data.append(line)

center=[0.,0.]
totN=0
pointsText=""
for i,line in enumerate(data):    
    pairs = [(pt[0],pt[1]) for pt in line]
    txtPairs=["%.6f %.6f"%(x,y) for x,y in pairs]
    ptsPkl = base64.b64encode(zlib.compress(str(txtPairs)))
    encoding,levels = glineenc.encode_pairs(pairs)
    encoding=encoding.replace('\\','\\\\')
    for pt in line:
        latit = pt[0]
        longit = pt[1]
        center[0] += latit
        center[1] += longit
        totN+=1
    if len(data)==1:
      pointsText+="""var polyline_%(idx)d=new google.maps.Polyline.fromEncoded({opacity:"%(lineOpacity).1f",color:"%(lineColor)s",weight:%(lineWidth)d,points:"%(encoding)s",levels:"%(levels)s",zoomFactor:32,numLevels:4}); var ptsArchive="%(ptsPkl)s"; /*decode from python with: zlib.decompress(base64.b64decode(ptsArchive))*/"""%locals()
    else:
      pointsText+="""var polyline_%(idx)d_%(i)d=new google.maps.Polyline.fromEncoded({opacity:"%(lineOpacity).1f",color:"%(lineColor)s",weight:%(lineWidth)d,points:"%(encoding)s",levels:"%(levels)s",zoomFactor:32,numLevels:4}); var ptsArchive_%(i)d="%(ptsPkl)s"; /*decode from python with: zlib.decompress(base64.b64decode(ptsArchive))*/"""%locals()
        

latit,longit=center
latit /= totN
longit /= totN
print >>outF,template%locals()
