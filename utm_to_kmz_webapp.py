import streamlit as st
import zipfile
from io import BytesIO
from pyproj import Proj, transform
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Set up projections
utm_proj = Proj(proj="utm", zone=40, ellps="WGS84", north=True)
wgs84_proj = Proj(proj="latlong", datum="WGS84")

def convert_utm_to_latlon(easting, northing):
    lon, lat = transform(utm_proj, wgs84_proj, easting, northing)
    return lon, lat

def generate_kml(points):
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")
    SubElement(document, "name").text = "Line and Points"

    for name, lon, lat in points:
        placemark = SubElement(document, "Placemark")
        SubElement(placemark, "name").text = name
        point = SubElement(placemark, "Point")
        SubElement(point, "coordinates").text = f"{lon},{lat},0"

    line_placemark = SubElement(document, "Placemark")
    SubElement(line_placemark, "name").text = "Line Path"
    linestring = SubElement(line_placemark, "LineString")
    SubElement(linestring, "tessellate").text = "1"
    coord_text = "\n".join([f"{lon},{lat},0" for _, lon, lat in points])
    SubElement(linestring, "coordinates").text = coord_text

    return minidom.parseString(tostring(kml)).toprettyxml(indent="  ")

def create_kmz(kml_content):
    kmz_buffer = BytesIO()
    with zipfile.ZipFile(kmz_buffer, 'w', zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_content)
    kmz_buffer.seek(0)
    return kmz_buffer

st.title("UTM Zone 40N to KMZ Converter")

input_text = st.text_area("Paste UTM coordinates (e.g., IN-DOF-01 E=231550.263 N=2711114.851)", height=200)

if st.button("Generate KMZ"):
    points = []
    for line in input_text.strip().splitlines():
        try:
            name_part, e_part, n_part = line.split()
            name = name_part
            easting = float(e_part.split('=')[1])
            northing = float(n_part.split('=')[1])
            lon, lat = convert_utm_to_latlon(easting, northing)
            points.append((name, lon, lat))
        except Exception as e:
            st.error(f"Error processing line: {line}\n{e}")

    if points:
        kml_content = generate_kml(points)
        kmz_file = create_kmz(kml_content)
        st.download_button("Download KMZ", kmz_file, file_name="coordinates.kmz")