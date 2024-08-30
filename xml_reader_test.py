from lxml import etree

# Parse the mzML file
tree = etree.parse("20240307_EB_dbgi_001195_01_01.mzML")
root = tree.getroot()

# Define the namespaces
namespaces = {
    "mzml": "http://psi.hupo.org/ms/mzml",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


# Access the sourceFile element within fileDescription
source_file = root.find(".//mzml:sourceFile", namespaces)
cv_param = source_file.find(".//mzml:cvParam", namespaces)

# Get the location attribute from the sourceFile element
location = source_file.get("location")
print(location)
file = source_file.get("name")
print(file)

# Print the fileDescription element as a string
print(etree.tostring(source_file, pretty_print=True).decode())
print(etree.tostring(cv_param, pretty_print=True).decode())
