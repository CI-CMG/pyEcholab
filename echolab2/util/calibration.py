# coding=utf-8

'''
Created on Mar 14, 2013

@author: zachary.berkowitz
'''

import datetime
from codecs import open
import re
import logging
import warnings

import pandas as pd
from xml.etree.ElementTree import ElementTree
log = logging.getLogger(__name__)

EL_OPT = '#pyEL'

ECS_SUFFIXES = {
    'AbsorptionCoefficient': '# (decibels per meter) [0.0000000..100.0000000]',
    'TwoWayBeamAngle': '# (decibels re 1 steradian) [-99.000000..-1.000000]',
    'Frequency': '# (kilohertz) [0.01..10000.00]',
    'Ek60TransducerGain' : '# (decibels) [1.0000..99.0000]',
    'TransmittedPulseLength': '# (milliseconds) [0.001..50.000]',
    'EK60SaCorrection': '# (decibels) [-99.9900..99.9900]',
    'SoundSpeed': '# (meters per second) [1400.00..1700.00]', 
    'TransmittedPower':  '# (watts) [1.00000..30000.00000]',
    'MajorAxisAngleOffset': '# (degrees) [-9.99..9.99]',
    'MajorAxisAngleSensitivity': '# [0.10..100.00]',
    'MinorAxisAngleOffset' :  '# (degrees) [-9.99..9.99]',
    'MinorAxisAngleSensitivity':  '# [0.10..100.00]',
    'MinorAxis3dbBeamAngle' : '# (degrees) [0.00..359.99]',
    'MajorAxis3dbBeamAngle': '# (degrees) [0.00..359.99]',
    EL_OPT + 'TransducerDepth': '# (meters) Depth of transducer face',
#    u'ChannelName': u'# ID String of transceiver',
}

EL_TO_ECS_TRANSLATION = {
    'absorption_coefficient':   ('AbsorptionCoefficient',       None),
    'equivalent_beam_angle':    ('TwoWayBeamAngle',             None),
    'frequency':                ('Frequency',                   lambda x: float(x)/1e3),
    'gain':                     ('Ek60TransducerGain',          None),
    'pulse_length':             ('TransmittedPulseLength',      lambda x: x * 1e3),
    'sa_correction':            ('EK60SaCorrection',            None),
    'sound_velocity':           ('SoundSpeed',                  None), 
    'transmit_power':           ('TransmittedPower',            None),
    'angle_offset_alongship':         ('MajorAxisAngleOffset',        None),
    'angle_sensitivity_alongship':    ('MajorAxisAngleSensitivity',   None),
    'angle_offset_athwartship' :      ('MinorAxisAngleOffset',        None),
    'angle_sensitivity_athwartship':  ('MinorAxisAngleSensitivity',   None),
    'beamwidth_athwartship':     ('MinorAxis3dbBeamAngle',       None),
    'beamwidth_alongship':       ('MajorAxis3dbBeamAngle',       None),
    
    #pyEcholab options
    'transducer_depth':         (EL_OPT + 'TransducerDepth',    None),
#    'channel_id':               (EL_OPT + u'ChannelName',        lambda x: codecs.decode(x, 'utf-8'))
#    'offset':                   (EL_OPT + u'Offset',             None,                   '# (samples) Offset of first recorded sample'),
#    'sample_interval':          (EL_OPT + u'SampleInterval',     None,                   '# (seconds) Sample interval'),
    #Ignored keys
    'pulse_length_table':       (None, None, None)
}

ECS_TO_EL_TRANSLATION = {
    'AbsorptionCoefficient':       ('absorption_coefficient',   float                 ),
    'TwoWayBeamAngle':             ('equivalent_beam_angle',    float                 ),
    'Frequency':                   ('frequency',                lambda x: float(x)*1e3),
    'Ek60TransducerGain':          ('gain',                     float                 ),
    'Offset':                      ('offset',                   float                 ),
    'SampleInterval':              ('sample_interval',          float                 ),
    'TransmittedPulseLength':      ('pulse_length',             lambda x: float(x) / 1e3),
    'EK60SaCorrection':            ('sa_correction',            float                 ),
    'SoundSpeed':                  ('sound_velocity',           float                 ),
    'TransmittedPower':            ('transmit_power',           float                 ),
    'MajorAxisAngleOffset':        ('angle_offset_alongship',         float                 ),
    'MajorAxisAngleSensitivity':   ('angle_sensitivity_alongship',    float                 ),
    'MinorAxisAngleOffset':        ('angle_offset_athwartship' ,      float                 ),
    'MinorAxisAngleSensitivity':   ('angle_sensitivity_athwartship',  float                 ),
    'MinorAxis3dbBeamAngle':       ('beamwidth_athwartship' ,    float                 ),
    'MajorAxis3dbBeamAngle':       ('beamwidth_alongship' ,      float                 ),
    #pyEcholab options
    EL_OPT + 'TransducerDepth':    ('transducer_depth', float)
}

XML_TO_EL_TRANSLATION = {
    'soundvelocity':                    ('sound_velocity',          int),
    'sampleinterval':                   ('sample_interval',         float),
    'absorptioncoefficient':            ('absorption_coefficient',  float),
    'sacorrectiontable':                ('sa_correction_table',     lambda x: list(map(float, x.strip('[]').split(';')))),
    'gain':                             ('gain',                    float),
    'equivalentbeamangle':              ('equivalent_beam_angle',   float),
    'pulselengthtable':                 ('pulse_length_table',      lambda x: list(map(float, x.strip('[]').split(';')))),
    'pulselength':                      ('pulse_length',            float),
    'transmitpower':                    ('transmit_power',          float),

    #Added later..
    'anglesoffsetalongship':            ('angle_offset_alongship',        float),
    'angleoffsetathwartship':           ('angle_offset_athwartship',      float),
    'anglesensitivityalongship':        ('angle_sensitivity_alongship',   float),
    'anglesensitivityathwartship':      ('angle_sensitivity_athwartship', float),
    'transducerdepth':                  ('angle_transducer_depth',        float)
}

def import_xml(xmlfile):

    global XML_TO_EL_TRANSLATION

    et = ElementTree()
    et.parse(xmlfile)

    calibration_dict = {38e3: {},
                        120e3: {}}


    temp_dict = {}
    freq = None

    for tag in et.iter():
        name = tag.tag
        value = tag.text.strip()

        if name == 'frequency':
            value = int(value)
            freq_dict = calibration_dict[value]
            freq_dict['frequency'] = value
            freq = value
            freq_dict.update(temp_dict)
            temp_dict = {}

        elif name in list(XML_TO_EL_TRANSLATION.keys()):
            translated_name, conv_func = XML_TO_EL_TRANSLATION[name]
            value = conv_func(value)
           
            if freq is None:
                temp_dict[translated_name] = value

            else:
                if translated_name in list(freq_dict.keys()):
                    freq = None
                    temp_dict = {translated_name: value}
                else:
                    freq_dict[translated_name] = value
            

    for freq in [38e3, 120e3]:
        indx = calibration_dict[freq]['pulse_length_table'].index(calibration_dict[freq]['pulse_length'])
        calibration_dict[freq]['sa_correction'] = float(calibration_dict[freq]['sa_correction_table'][indx])

        del calibration_dict[freq]['sa_correction_table']

        if 'offset' not in list(calibration_dict[freq].keys()):
            calibration_dict[freq]['offset'] = 0

    return calibration_dict


def xml_to_ecs(xmlfile, echosounder_ids=[(38000, 'GPT  38 kHz 009072067bdf 1 ES38B')]):

    ECS_HEADER=\
"""
#========================================================================================#
#               ECHOVIEW CALIBRATION SUPPLEMENT (.ECS) FILE (SimradEK60Raw)              #
#                                    8/8/2012 16:54:35                                   #
#========================================================================================#
#       +----------+   +-----------+   +----------+   +-----------+   +----------+       #
#       | Default  |-->| Data File |-->| Fileset  |-->| SourceCal |-->| LocalCal |       #
#       | Settings |   | Settings  |   | Settings |   | Settings  |   | Settings |       #
#       +----------+   +-----------+   +----------+   +-----------+   +----------+       #
# - Settings to the right override those to their left.                                  #
# - See the Help file page "About calibration".                                          #
# - Uses linearized avg values from June & Aug cal (38 kHz), and June cal (120 kHz)      #
#========================================================================================#

#========================================================================================#
#      THIS FILE WAS CREATED USING pyAVO AND CONTAINS  ADDITIONAL PARAMTERS NOT USED     #
#      IN ECHOVIEW.                                                                      #
#                                                                                        #
#      ANY COMMENT BEGINNING WITH '{0}' MUST REMAIN COMMENTED.{1}#  
#      IT WILL BE PARSED BY THE INTENDED PROGRAM, BUT AS AN ILLEGAL OPTION WILL CAUSE    #
#      ERRORS IN ECHOVIEW IF 'ENABLED'                                                   #
#                                                                                        #
#                                                                                        #
#========================================================================================#                   

Version 1.00

""".format(AVOOPT, ' '*(30-len(AVOOPT)))

    translation_table = {
    'absorption_coefficient':   ('AbsorptionCoefficient',       None,                   '# (decibels per meter) [0.0000000..100.0000000]'),
    'equivalent_beam_angle':    ('TwoWayBeamAngle',             None,                   '# (decibels re 1 steradian) [-99.000000..-1.000000]'),
    'frequency':                ('Frequency',                   lambda x: float(x)/1e3, '# (kilohertz) [0.01..10000.00]'),
    'gain':                     ('Ek60TransducerGain',          None,                   '# (decibels) [1.0000..99.0000]'),
#    'offset':                   (AVOOPT + 'Offset',             None,                   '# (samples) Offset of first recorded sample'),
#    'sample_interval':          (AVOOPT + 'SampleInterval',     None,                   '# (seconds) Sample interval'),
    'pulse_length':             ('TransmittedPulseLength',      lambda x: x * 1e3,      '# (milliseconds) [0.001..50.000]'),
    'sa_correction':            ('EK60SaCorrection',            None,                   '# (decibels) [-99.9900..99.9900]'),
    'sound_velocity':           ('SoundSpeed',                  None,                   '# (meters per second) [1400.00..1700.00]'), 
    'transmit_power':           ('TransmittedPower',            None,                   '# (watts) [1.00000..30000.00000]'),
    'alongship_offset':         ('MajorAxisAngleOffset',        None,                   '# (degrees) [-9.99..9.99]'),
    'alongship_sensitivity':    ('MajorAxisAngleSensitivity',   None,                   '# [0.10..100.00]'),
    'athwartship_offset' :      ('MinorAxisAngleOffset',        None,                   '# (degrees) [-9.99..9.99]'),
    'athwartship_sensitivity':  ('MinorAxisAngleSensitivity',   None,                   '# [0.10..100.00]'),
    'beamwith_athwartship':     ('MinorAxis3dbBeamAngle',       None,                    '# (degrees) [0.00..359.99]'  ),
    'beamwith_alongship':       ('MajorAxis3dbBeamAngle',       None,                    '# (degrees) [0.00..359.99]'),
#    'transducer_depth':         (AVOOPT + 'TransducerDepth',    None,                   '# (meters)  Depth of transducer below surface'),
    #Ignored keys
    'pulse_length_table':       (None, None, None)
    }
    cal_dict = import_xml(xmlfile)

    source_cal_txt =\
"""


#========================================================================================#
#                                   SOURCECAL SETTINGS                                   #
#========================================================================================#
"""

    sound_speeds = []
    for xml_cal in list(cal_dict.values()):
        sound_speeds.append(xml_cal['sound_velocity'])

    if len(set(sound_speeds)) > 1:
        SOURCE_SOUND_SPEEDS = True
    else:
        SOURCE_SOUND_SPEEDS = False

    for txcvr_indx, (frequency_hz, txcvr_id) in enumerate(echosounder_ids):
        
        xml_cal = cal_dict[frequency_hz]

        source_cal_txt += '\nSourceCal T{0:d}\n'.format(txcvr_indx + 1)
        source_cal_txt += '    {id_key} = {id} # {suffix}\n'.format(id_key=AVOOPT + 'ChannelID',
            id=txcvr_id, 
            suffix='Transceiver ID string')

        for xml_key in sorted(xml_cal.keys()):
            ecs_key, manip_func, ecs_suffix = translation_table[xml_key]
            value = xml_cal[xml_key]

            if xml_key == 'sound_velocity' and not SOURCE_SOUND_SPEEDS:
                continue

            if ecs_key is None:
                continue

            if manip_func is not None:
                value = manip_func(value)

            source_cal_txt += '    {ecs_key} = {value} {ecs_suffix}\n'.format(ecs_key=ecs_key,
                value=value, ecs_suffix=ecs_suffix)


    fileset_txt = \
"""
#========================================================================================#
#                                    FILESET SETTINGS                                    #
#========================================================================================#

"""
    if not SOURCE_SOUND_SPEEDS:
        ecs_key, manip_func, ecs_suffix = translation_table['sound_velocity']
        
        if manip_func is not None:
            value = manip_func(sound_speeds[0])
        else:
            value = sound_speeds[0]

        fileset_txt += '{ecs_key} = {value} {ecs_suffix}\n'.format(ecs_key=ecs_key,
                value=value, ecs_suffix=ecs_suffix)

    local_settings = \
"""
#========================================================================================#
#                                    LOCALCAL SETTINGS                                   #
#========================================================================================#


"""

    return ECS_HEADER + fileset_txt + source_cal_txt + local_settings

def import_ecs(ecs_filename):
    '''
from echolab.util.calibration import ECS_SUFFIXES
    :param ecs_filename: Filename to import
    :type ecs_filename: str
    
    :returns: dict
    
    Imports an Echoview .ecs file containing calibration values and
    returns a dict
    '''
    
    AVOOPT = '#pyAVO'

#    translation_table = {
#    u'AbsorptionCoefficient':       ('absorption_coefficient',   float                 ),
#    u'TwoWayBeamAngle':             ('equivalent_beam_angle',    float                 ),
#    u'Frequency':                   ('frequency',                lambda x: float(x)*1e3),
#    u'Ek60TransducerGain':          ('gain',                     float                 ),
#    u'Offset':                      ('offset',                   float                 ),
#    u'SampleInterval':              ('sample_interval',          float                 ),
#    u'TransmittedPulseLength':      ('pulse_length',             lambda x: float(x) / 1e3),
#    u'EK60SaCorrection':            ('sa_correction',            float                 ),
#    u'SoundSpeed':                  ('sound_velocity',           float                 ),
#    u'TransmittedPower':            ('transmit_power',           float                 ),
#    u'MajorAxisAngleOffset':        ('alongship_offset',         float                 ),
#    u'MajorAxisAngleSensitivity':   ('alongship_sensitivity',    float                 ),
#    u'MinorAxisAngleOffset':        ('athwartship_offset' ,      float                 ),
#    u'MinorAxisAngleSensitivity':   ('athwartship_sensitivity',  float                 ),
#    u'MinorAxis3dbBeamAngle':       ('beamwith_athwartship' ,    float                 ),
#    u'MajorAxis3dbBeamAngle':       ('beamwith_alongship' ,      float                 ),
    
    #pyAVO custom values
#    u'ChannelID'                 :   ('channel_id', str),
#    u'SampleInterval':               ('sample_interval', float),
#    u'Offset':                       ('offset', int),
#    u'TransducerDepth':              ('transducer_depth', float)

#    }

    file_cals = {}
    source_cals = {}
    current_source = {}
    _FILE = 1
    _SOURCE = 2

    PARSING = _FILE

    with open(ecs_filename, mode='r', encoding='utf-8') as ecs_fid:
        for line in ecs_fid:

            line = line.strip('\ufeff :;\n\t\r')
            if line.startswith(AVOOPT):
                line = line[len(AVOOPT):].strip(' :;\n\t')

            if line.startswith('#') or len(line) == 0:
                continue

            if line.lower().startswith('ver'):
                continue

            keyword, sep, value = line.partition('=')
            keyword = keyword.strip()
            value = value.partition('#')[0].strip()
            
            if sep == '=':
                try:
                    avo_key, conv_func = ECS_TO_EL_TRANSLATION[keyword]
                except KeyError:
                    warnings.warn('Ignored unknown keyword in ECS file: %s' %(keyword),
                        SyntaxWarning)
                    continue
                
                if PARSING == _SOURCE:
                    current_source[avo_key] = conv_func(value)
                
                elif PARSING == _FILE:
                    file_cals[avo_key] = conv_func(value)



            elif 'source' in keyword.lower():
                try:
                    transceiver_num = re.search(r'T([0-9]+)', keyword).group(1)
                except AttributeError:
                    raise ValueError('Unable to parse transceiver number from %s' %(keyword))
                transceiver_num = int(transceiver_num)
                
                if current_source != {}:
                    prev_txcver = current_source.pop('channel_num')
                    source_cals[prev_txcver] = current_source.copy()
                    current_source = {'channel_num': transceiver_num}
                else:
                    current_source = {'channel_num': transceiver_num}

                PARSING = _SOURCE

            else:
                log.warning('Unable to process line: %s', line)


    if PARSING == _SOURCE:
        if current_source != {}:
            channel_num = current_source.pop('channel_num')
            source_cals[channel_num] = current_source.copy()
            current_source = {}

    for key, value in list(file_cals.items()):
        for cal in list(source_cals.values()):
            cal.update({key: value})

    return source_cals

def export_ecs(calibration):
    '''
    :param calibration: Calibration dictionary
    :type calibration: dict
    
    :returns: Unicode string.
    '''
    global EL_OPT
    global EL_TO_ECS_TRANSLATION
    global ECS_SUFFIXES
    
    datestr = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
#    datestr = u'#' + u' ' * (88 - len(datestr))/2 + datestr + u' ' * (88 - len(datestr))/2 + datestr + '#'
    
    ECS_HEADER=\
"""
#========================================================================================#
#               ECHOVIEW CALIBRATION SUPPLEMENT (.ECS) FILE (SimradEK60Raw)              #
#{date: ^88s}#
#========================================================================================#
#       +----------+   +-----------+   +----------+   +-----------+   +----------+       #
#       | Default  |-->| Data File |-->| Fileset  |-->| SourceCal |-->| LocalCal |       #
#       | Settings |   | Settings  |   | Settings |   | Settings  |   | Settings |       #
#       +----------+   +-----------+   +----------+   +-----------+   +----------+       #
# - Settings to the right override those to their left.                                  #
# - See the Help file page "About calibration".                                          #
#========================================================================================#

#========================================================================================#
#      THIS FILE WAS CREATED USING pyEcholab AND CONTAINS  ADDITIONAL PARAMTERS NOT USED #
#      IN ECHOVIEW.                                                                      #
#                                                                                        #
#      ANY COMMENT BEGINNING WITH '{EL_OPT}' MUST REMAIN COMMENTED.{EL_SPACE}#
#      IT WILL BE PARSED BY THE INTENDED PROGRAM, BUT AS AN ILLEGAL OPTION WILL CAUSE    #
#      ERRORS IN ECHOVIEW IF 'ENABLED'                                                   #
#        (AN EXTRA '#', i.e. #{EL_OPT} WILL DISABLE ECHOLAB PARAMS){EL_SPACE}#
#                                                                                        #
#                                                                                        #
#========================================================================================#                   

Version 1.00

""".format(EL_OPT=EL_OPT, EL_SPACE=' '*(30-len(EL_OPT)), date=datestr)

#    translation_table = {
#    'absorption_coefficient':   (u'AbsorptionCoefficient',       None,                   '# (decibels per meter) [0.0000000..100.0000000]'),
#    'equivalent_beam_angle':    (u'TwoWayBeamAngle',             None,                   '# (decibels re 1 steradian) [-99.000000..-1.000000]'),
#    'frequency':                (u'Frequency',                   lambda x: float(x)/1e3, '# (kilohertz) [0.01..10000.00]'),
#    'gain':                     (u'Ek60TransducerGain',          None,                   '# (decibels) [1.0000..99.0000]'),
#    'pulse_length':             (u'TransmittedPulseLength',      lambda x: x * 1e3,      '# (milliseconds) [0.001..50.000]'),
#    'sa_correction':            (u'EK60SaCorrection',            None,                   '# (decibels) [-99.9900..99.9900]'),
#    'sound_velocity':           (u'SoundSpeed',                  None,                   '# (meters per second) [1400.00..1700.00]'), 
#    'transmit_power':           (u'TransmittedPower',            None,                   '# (watts) [1.00000..30000.00000]'),
#    'alongship_offset':         (u'MajorAxisAngleOffset',        None,                   '# (degrees) [-9.99..9.99]'),
#    'alongship_sensitivity':    (u'MajorAxisAngleSensitivity',   None,                   '# [0.10..100.00]'),
#    'athwartship_offset' :      (u'MinorAxisAngleOffset',        None,                   '# (degrees) [-9.99..9.99]'),
#    'athwartship_sensitivity':  (u'MinorAxisAngleSensitivity',   None,                   '# [0.10..100.00]'),
#    'beamwith_athwartship':     (u'MinorAxis3dbBeamAngle',       None,                   '# (degrees) [0.00..359.99]'  ),
#    'beamwith_alongship':       (u'MajorAxis3dbBeamAngle',       None,                   '# (degrees) [0.00..359.99]'),
#    #Ignored keys
#    'pulse_length_table':       (None, None, None)
#    }


    fileset_txt = \
"""
#========================================================================================#
#                                    FILESET SETTINGS                                    #
#========================================================================================#

"""

    source_txt =\
"""


#========================================================================================#
#                                   SOURCECAL SETTINGS                                   #
#========================================================================================#
"""

    local_txt = \
"""
#========================================================================================#
#                                    LOCALCAL SETTINGS                                   #
#========================================================================================#


"""
    
#    suffix_dict = {}
#    for ecs_key, suffix in ECS_SUFFIXES.items():
#        suffix_dict[ecs_key] = suffix
        
    ecs_cal_dict = {}
    for source_num, cal in list(calibration.items()):
        source_name = 'SourceCal T{0:d}'.format(source_num)
        source_cal = ecs_cal_dict.setdefault(source_name, {})
        for param, value in list(cal.items()):
            if param in EL_TO_ECS_TRANSLATION:
                ecs_key, conv_func = EL_TO_ECS_TRANSLATION[param]
                if conv_func is not None:
                    value = conv_func(value)
                
                source_cal[ecs_key] = value

            else:
                warnings.warn("Calibration key: %s does not match a valid ECS key" %(param),
                    SyntaxWarning)
                
    ecs_cal_df = pd.DataFrame(ecs_cal_dict)
    
    
    #Find shared values
    shared_df = ecs_cal_df.dropna().T
    file_params = {}
    for col in shared_df.columns:
        if len(shared_df[col].unique()) == 1:
            file_params[col] = shared_df[col][0]

    
    file_params_txt = ''
    for key, value in list(file_params.items()):
        file_params_txt += '{key} = {value} {suffix}\n'.format(key=key,
                value=value, suffix=ECS_SUFFIXES[key])
    

    #Remove shared 
    ecs_cal_df = ecs_cal_df.drop(list(file_params.keys()), axis=0)
    
    source_params_txt = ''
    for source_name in ecs_cal_df.columns:
        source_params_txt += source_name + '\n'
        source_cal = ecs_cal_df[source_name].dropna()
        
        for key in sorted(ECS_SUFFIXES.keys()):
            
            if key in file_params:
                continue
            
            elif key in source_cal:
                source_params_txt += '\t{key} = {value} {suffix}\n'.format(key=key,
                    value=source_cal[key], suffix=ECS_SUFFIXES[key])
            else:
                source_params_txt += '\t#{key} = ... {suffix}\n'.format(key=key,
                    suffix=ECS_SUFFIXES[key])
        
        source_params_txt += '\n'
            
    return ECS_HEADER + fileset_txt + file_params_txt +\
            source_txt + source_params_txt + local_txt
 
