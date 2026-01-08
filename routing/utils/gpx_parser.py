import xml.etree.ElementTree as ET
import requests
from io import BytesIO

def parse_gpx_from_url(gpx_url):
    response = requests.get(gpx_url, timeout=15)
    response.raise_for_status()

    tree = ET.parse(BytesIO(response.content))
    root = tree.getroot()

    namespace = {'default': 'http://www.topografix.com/GPX/1/1'}
    points = []

    for trk in root.findall('default:trk', namespace):
        for trkseg in trk.findall('default:trkseg', namespace):
            for trkpt in trkseg.findall('default:trkpt', namespace):
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))

                ele_tag = trkpt.find('default:ele', namespace)
                ele = float(ele_tag.text) if ele_tag is not None else 0.0

                points.append((lat, lon, ele))

    return points

