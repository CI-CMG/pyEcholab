from util.simrad_raw_file import RawSimradFile


filename = 'C:/Users/rick.towler/Work/AFSCGit/pyEcholab/examples/data/EK60/DY1706_EK60-D20170609-T005736.bot'

#  open the file
fid =  RawSimradFile(filename, 'r')

#  first datagram is a config datagram
config_datagram = fid.read(1)
print(config_datagram)
datagram = fid.read(1)
datagram = fid.read(1)
