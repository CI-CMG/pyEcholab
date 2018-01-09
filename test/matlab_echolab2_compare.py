# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 09:01:10 2014

@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by the MATLAB based echolab toolbox using a common raw file
as input.

I have included a comparison to Echoview (EV) 5.4 Sv output since Echoview will
output Sv values to .mat format. Note that pyEcholab behaves almost identically
to the MATLAB echolab package and like it's MATLAB based brother, it too differs
from Echoview between the 3rd and 7th EV samples (4th and 8th pyEcholab samples.)
The difference is small starting around -0.004 dB with the 3rd sample reaching
a maximum of -0.017 dB at the 7th sample. After the 7th sample results are (or
should be) virtually identical.

"""

from echolab2.instruments import EK60
import numpy as np
from matplotlib import pyplot as plt
import h5py
import hashlib
import scipy.io


#  PLOT THE RESULTS?
#  set this variable to True to plot the results
plot_figs = True

#  define the paths to the reference data files
reference_input = [[38000,
                    './data/echolab_data_38kHz.mat',
                    './data/echolab_data_38kHz.mat.md5'],
                   [120000,
                   './data/echolab_data_120kHz.mat',
                   './data/echolab_data_120kHz.mat.md5']]
raw_filename = ['./data/test_data.raw',
                './data/test_data.raw.md5']
ev_filenames = [['./data/ev_data_38kHz.mat',
                 './data/ev_data_38kHz.mat.md5'],
                ['./data/ev_data_120kHz.mat',
                 './data/ev_data_120kHz.mat.md5']]



def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "r+b") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hash.update(block)
    return hash.hexdigest()


def print_difference(difference, test):
    print(test)
    print('    Minimum difference: %4.5f' % (difference.min()))
    print('    Maximum difference: %4.5f' % (difference.max()))


def plot_data(ref_data, el_data, diff_data, y, x, d_title, cb_label, d_label,
              title, ev_data=np.array([])):

    extents = [x[0], x[1], y[0], y[1]]

    fig = plt.figure(figsize=(11,7))
    fig.suptitle(title, fontsize=36)

    ax = plt.subplot(2,2,1)
    img = ax.imshow(ref_data,
              interpolation='nearest',
              extent=extents)
    ax.set_xlabel('range (m)')
    ax.set_ylabel('ping')
    cb = plt.colorbar(img, ax=ax)
    cb.set_label(d_label)
    plt.title('MATLAB Reference Data')

    ax = plt.subplot(2,2,2)
    img = ax.imshow(el_data,
              interpolation='nearest',
              extent=extents)
    ax.set_xlabel('range (m)')
    ax.set_ylabel('ping')
    cb = plt.colorbar(img, ax=ax)
    cb.set_label(d_label)
    plt.title('pyEcholab2 Data')

    ax = plt.subplot(2,2,3)
    img = ax.imshow(diff_data,
              interpolation='nearest',
              vmin=diff_data.min(),
              vmax=diff_data.max(),
              extent=extents)
    ax.set_xlabel('range (m)')
    ax.set_ylabel('ping')
    cb = plt.colorbar(img, ax=ax)
    cb.set_label(cb_label)
    plt.title(d_title)

    if (ev_data.size > 0):
        ax = plt.subplot(2,2,4)
        img = ax.imshow(ev_data,
                  interpolation='nearest',
                  vmin=diff_data.min(),
                  vmax=diff_data.max(),
                  extent=extents)
        ax.set_xlabel('range (m)')
        ax.set_ylabel('ping')
        cb = plt.colorbar(img, ax=ax)
        cb.set_label('Sv difference')
        plt.title('Echoview/pyEcholab Sv difference')

    text = 'Minimum difference: %4.5f' % (diff_data.min())
    plt.figtext(0.15, 0.03, text, fontsize=14)
    text = 'Maximum difference: %4.5f' % (diff_data.max())
    plt.figtext(0.55, 0.03, text, fontsize=14)

    return fig



if __name__ == "__main__":

    #  check the reference input file checksums
#    for i in range(2):
#        print('Verifying checksum for %s' % (reference_input[i][1]))
#        calc_cksum = md5sum(reference_input[i][1])
#
#        with open(reference_input[i][2]) as f:
#            ref_cksum = f.readlines()
#        if (ref_cksum[0] == calc_cksum):
#            print('Checksum is OK')
#        else:
#            raise IOError('Checksums do not match!')
#
#        #  check the EV file checksum
#        print('Verifying checksum for %s' % (ev_filenames[i][0]))
#        calc_cksum = md5sum(ev_filenames[i][0])
#
#        with open(ev_filenames[i][1]) as f:
#            ref_cksum = f.readlines()
#        if (ref_cksum[0] == calc_cksum):
#            print('Checksum is OK')
#        else:
#            raise IOError('Echoview Sv Export file checksum does not match!')


    #  check the raw file checksum
#    print('Verifying checksum for %s' % (raw_filename[0]))
#    calc_cksum = md5sum(raw_filename[0])
#
#    with open(raw_filename[1]) as f:
#        ref_cksum = f.readlines()
#    if (ref_cksum[0] == calc_cksum):
#        print('Checksum is OK')
#    else:
#        raise IOError('Raw file checksum does not match!')


    #  read in the .raw data file
    print('Reading the raw file %s' % (raw_filename[0]))
    ek60 = EK60.EK60()
    ek60.read_raw(raw_filename[0])

    #  load up the reference data
    ref_data = {}
    for i in reference_input:

        #  read the data for this channel
        f = h5py.File(i[1])
        print('Reading %s' % (i[1]))

        #  stick it in a dict - orient the data to match pyEcholab
        ref_data[i[0]] = {'power':((f.get('power').value)),
                          'sv':((f.get('sv').value)),
                          'sv_linear':((f.get('sv_linear').value)),
                          'sp':((f.get('sp').value)),
                          'sp_linear':((f.get('sp_linear').value)),
                          'alongship':((f.get('alongship').value)),
                          'alongship_e':((f.get('alongship_e').value)),
                          'athwartship':((f.get('athwartship').value)),
                          'athwartship_e':((f.get('athwartship_e').value)),
                          'ping_number':f.get('ping_number').value,
                          'range':f.get('range').value,
                          'frequency':f.get('frequency').value}
        f.close()

    #  compare data for the two channels
    for i in range(1):

        #  get a reference to this channel's raw_data
        raw_data = ek60.get_rawdata(i+1)


        # set up the figure extents
        x = [ref_data[reference_input[i][0]]['ping_number'].min(),
             ref_data[reference_input[i][0]]['ping_number'].max()]
        y = [ref_data[reference_input[i][0]]['range'].max(),
             ref_data[reference_input[i][0]]['range'].min()]


        #  extract the power data into a processed_data object
        data = raw_data.get_power()
        title = '%3.0f kHz Power results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['power'] - data.power
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['power'], data.power,
                            difference, x, y, 'power difference', 'Difference in dB',
                            'Power', title)
            plt.show(block=True)


        #  get the Sv array for this channel
        #  extract the power data into a processed_data object
        data = raw_data.get_sv(insert_into=data, keep_power=True)
        title = '%3.0f kHz Sv results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['sv'] - data.Sv
        print_difference(difference, title)

        #  read in the Echoview exported Sv (EV exports this in an older matlab
        #  format so we use scipy.io.loadmat to read it)
        ev_data = scipy.io.loadmat(ev_filenames[i][0])

        #  calculate the difference between Echoview's Sv output and pyEcholab. Note
        #  that since we selected to not drop the zero range sample we must remove
        #  the first sample from our pyEcholab data since Echoview always drops
        #  the first sample.
        ev_difference = ev_data['Data_values'] - data.Sv[:,1:]
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['sv'], data.Sv,
                            difference, x, y, 'Sv difference', 'Difference in dB',
                            'Sv', title, ev_data=ev_difference)
            plt.show(block=True)

            ev_ping = ev_data['Data_values'][10,:]
            fig = plt.plot(np.arange(ev_ping.shape[0]), ev_ping, label='Echoview', color='blue', linewidth=2)
            fig = plt.plot(np.arange(data.Sv[10,1:].shape[0]), data.Sv[10,1:], label='pyEcholab2', color='red')
            plt.legend()
            plt.show(block=True)



        #  get the sv array for this channel
        data = raw_data.get_sv(insert_into=data, linear=True)
        title = '%3.0f kHz sv results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['sv_linear'] - data.sv
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['sv_linear'], data.sv,
                            difference, x, y, 'sv difference', 'Difference',
                            'sv', title)
            plt.show(block=True)


        #  get the Sp array for this channel
        data = raw_data.get_sp(insert_into=data)
        title = '%3.0f kHz Sp results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['sp'] - data.Sp
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['sp'], data.Sp,
                            difference, x, y, 'Sp difference', 'Difference in dB',
                            'Sp', title)
            plt.show(block=True)

        #  get the sp array for this channel
        data = raw_data.get_sp(insert_into=data, linear=True)
        title = '%3.0f kHz sp results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['sp_linear'] - data.sp
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['sp_linear'], data.sp,
                            difference, x, y, 'sp difference', 'Difference',
                            'sp', title)
            plt.show(block=True)

        #  get the physical angles array
        data = raw_data.get_physical_angles(insert_into=data)
        #  plot alongship angles
        title = '%3.0f kHz alongship angle results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['alongship'] - data.angles_alongship
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['alongship'],
                            data.angles_alongship, difference, x, y,
                            'alongship difference', 'Difference in degrees',
                            'angle', title)
            plt.show(block=True)

        #  plot athwartship angles
        title = '%3.0f kHz athwartship angle results' % (ref_data[reference_input[i][0]]['frequency'] / 1000)
        difference = ref_data[reference_input[i][0]]['athwartship'] - data.angles_athwartship
        print_difference(difference, title)
        if (plot_figs):
            fig = plot_data(ref_data[reference_input[i][0]]['athwartship'],
                            data.angles_athwartship, difference, x, y,
                            'athwartship difference', 'Difference in degrees',
                            'angle', title)
            plt.show(block=True)
