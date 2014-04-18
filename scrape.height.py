import simplejson,urllib,random
idx = random.randint(1,10000000)
import sys,re,os,datetime

CHART_BASE_URL = 'http://chart.apis.google.com/chart'
ELEVATION_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
tInterval=1800
pltWidth=400
pltHeight=200

if len(sys.argv)==3 and sys.argv[2]!='-' and os.path.splitext(sys.argv[2])[-1]!='.gpx':
    outF = file(sys.argv[2],'w+')
    inNames = [sys.argv[1]]
else:
    outF = sys.stderr
    inNames = sys.argv[1:]

from xml.etree import cElementTree as ET
data=[]
for inF in inNames:
    line=[]
    times=[]
    inF = file(inF,'ru')
    et = ET.ElementTree(file=inF)
    vers='.//{http://www.topografix.com/GPX/1/1}'
    pts = et.findall(vers+'trkpt')
    if not pts:
        vers='.//{http://www.topografix.com/GPX/1/0}'        
        pts = et.findall(vers+'trkpt')
        if not pts:
            vers='.//{http://www.topografix.com/GPX/1/0}'
            pts = et.findall(vers+'rtept')
            if not pts:
                raise ValueError,'could not find any points'
    #for pt in pts:
    #    line.append((float(pt.get('lat')),float(pt.get('lon'))))
    for pt in pts:
        line.append('%s,%s'%(pt.get('lat'),pt.get('lon')))
        tme=pt.find(vers+'time')
        if tme:
            t = tme.text
            times.append(datetime.datetime.strptime(t,'%Y-%m-%dT%H:%M:%SZ'))
    data.append((line,times))

from math import *
def geodist(p1,p2):
    """
    formula from here:
    http://www.movable-type.co.uk/scripts/latlong.html
    """
    p1 = [float(x) for x in p1.split(',')]
    lat1,lon1=p1
    p2 = [float(x) for x in p2.split(',')]
    lat2,lon2=p2
    R = 6371
    dLat = pi*(lat2-lat1)/180.
    dLon = pi*(lon2-lon1)/180.
    lat1 = pi*lat1/180.
    lat2 = pi*lat2/180.
    a = sin(dLat/2) * sin(dLat/2) + \
        sin(dLon/2) * sin(dLon/2) * cos(lat1) * cos(lat2)
    c = 2 * atan2(sqrt(a), sqrt(1-a));
    d = R * c    
    return d
     

html="""<html>
  <head>
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load('visualization', '1',{'packages':['corechart']});
      google.setOnLoadCallback(drawVisualizations);

      function drawVisualizations() {
        var divs = document.getElementsByTagName('div');
        for(var i=0;i<divs.length;i++){
          var div = divs[i];
          if( div.className.search('gpsplt')!=-1){
            var idx = div.className.split('_')[1];
            var dtbl = eval('dtbl_'+idx);
            drawVisualization(dtbl);
          }
        }
      }
      function drawVisualization(dT) {
        chart=new google.visualization.ComboChart(document.getElementById('vis_div'));
        options={seriesType:'line',
                 series:{2:{type:'scatter'},3:{type:'scatter'}},
                 vAxis:{title:'Height'},
                 hAxis:{title:'Distance'},
                 legend:{position:'none'}
                };
        chart.draw(dT,options);
      }
    </script>
  </head>
  <body style="font-family: Arial;border: 0 none;">
    <script type="text/javascript">
var dtbl_%(idx)d;
dtbl_%(idx)d = new google.visualization.DataTable();
dtbl_%(idx)d.addColumn('number','Distance');
dtbl_%(idx)d.addColumn('number','Height');
dtbl_%(idx)d.addColumn('number','HeightInterval');
dtbl_%(idx)d.addColumn('number','Interval');
dtbl_%(idx)d.addRows([
%(dRows)s
]);
    </script>
    <div id="vis_div" class="gpsplt_%(idx)d" style="width: %(pltWidth)dpx; height: %(pltHeight)dpx;"></div>
  </body>
</html>
"""
clip="""
    <script type="text/javascript">
var dtbl_%(idx)d;
dtbl_%(idx)d = new google.visualization.DataTable();
dtbl_%(idx)d.addColumn('number','Distance');
dtbl_%(idx)d.addColumn('number','Height');
dtbl_%(idx)d.addColumn('number','HeightInterval');
dtbl_%(idx)d.addColumn('number','Interval');
dtbl_%(idx)d.addRows([
%(dRows)s
]);
    </script>
    <div id="vis_div" class="gpsplt_%(idx)d" style="width: %(pltWidth)dpx; height: %(pltHeight)dpx;"></div>
"""
dRows=[]
dists=None
minElev=100000
for i,(line,times) in enumerate(data):
    pieces = []
    for j in range(0,len(line),50):
        splitPieces = [x.split(',') for x in line[j:min(j+50,len(line))]]
        args = {'sensor':'false',
                'locations':'|'.join(['%.6f,%.6f'%(float(x),float(y)) for x,y in splitPieces])}
        url = ELEVATION_BASE_URL + '?' + urllib.urlencode(args)
        rawd=urllib.urlopen(url).read()
        pieces.append(simplejson.loads(rawd))
    pts = []
    for piece in pieces:
        pts.extend(piece['results'])
    if times:
        stime=times[0]
        shiftimes=[(x-stime).seconds for x in times]
    if dists is None:
        dists=[0]
    else:
        dists=[dists[-1]]
    for j in range(1,len(line)):
        d = dists[j-1]+geodist(line[j-1],line[j])
        dists.append(d)
    if times:
        assert len(dists)==len(shiftimes)    
        intervals=[]
        for j in range(1,len(shiftimes)):
            t1 = shiftimes[j-1]
            t2 = shiftimes[j]
            if (t2//tInterval)>(t1//tInterval):
                intervals.append(j)
    elevs=[x['elevation'] for x in pts]
    minElev = min(minElev,min(elevs))
    sis1=['null']*len(dists)
    sis2=['null']*len(dists)
    if times:
        for interval in intervals:
            sis1[interval]='%.1f'%elevs[interval]
            sis2[interval]='%.1f'%minElev
        sis2[0]=str(minElev)
    rowD = zip(dists,elevs,sis1,sis2)
    dRows.append(','.join(["[%.2f,%.1f,%s,%s]"%(x,y,z,a) for x,y,z,a in rowD]))
dRows = ','.join(dRows)
print clip%locals()

        
