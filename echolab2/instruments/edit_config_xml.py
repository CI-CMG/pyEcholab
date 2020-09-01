

#import xml.etree.ElementTree as ET
from lxml import etree as ET


#xmlstr = ElementTree.tostring(et, encoding='utf8', method='xml')

filename = 'C:/Users/rick.towler/Work/AFSCGit/pyEcholab/echolab2/instruments/resources/Saildrone_CW_Complex_Configuration.xml'
outfile = 'C:/Temp_EK_Test/test_xml'


tree = ET.parse(filename)
root = tree.getroot()



header = tree.find("./Header")
header.set("Copyright","NUNYA!")


tree = ET.ElementTree(root)
tree.write(outfile, encoding='utf8', method='xml')

#if bbb:

#for AAA in root.findall('AAA'):
#    if AAA.find('CCC'):
#        BBB = AAA.find('CCC').find('BBB')
#        BBB.text = '33333' + BBB.text
#
#tree.write('C:\\test\\python test\\output.xml')

#outfile = 'C:/Temp_EK_Test/test_xml'
#
#root = ET.Element("Configuration")
#
#head = ET.SubElement(root, "Header")
#head.set("Copyright", "Copyright(c) Kongsberg Maritime AS, Norway")
#head.set("ApplicationName", "EKauto")
#head.set("Version", "3.5.0")
#head.set("FileFormatVersion", "1.20")
#head.set("TimeBias", "0")




#title = ET.SubElement(head, "title")
#title.text = "Page Title"
#
#body = ET.SubElement(root, "body")
#body.set("bgcolor", "#ffffff")
#
#body.text = "Hello, World!"

# wrap it in an ElementTree instance, and save as XML
#tree = ET.ElementTree(root)
#tree.write(outfile)
