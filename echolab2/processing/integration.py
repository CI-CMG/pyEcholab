# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

# THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
# AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
# IS. THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
# OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
# AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
# THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
# DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assessment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np


class results(object):


    """
    

    """

    def __init__(self, interval_length=0.5, interval_axis='trip_distance_nmi',
            layer_thickness=10, layer_axis='depth', data=None, color=[0.0, 0.0, 0.0],
                 name='grid', linestyle='solid', linewidth=1.0,
                 round_interval_starts=True):
        """Initializes a new integration.results class object. Results objects contain
        the results from an integration operation.

    Arguments:

        interval_length (int OR float OR timedelta64): Specify the length of the grid intervals in
                units specified in the interval_axis keyword argument.
        

        """
        super(results, self).__init__()


class integrator(object):

    """
    

    """

    def __init__(self, min_threshold=-70, min_threshold_applied=False, 
            max_threshold=0, max_threshold_applied=False):
        """Initializes a new integration class object.

    Arguments:

        interval_length (int OR float OR timedelta64): Specify the length of the grid intervals in
                units specified in the interval_axis keyword argument.
        

        """
        super(integrator, self).__init__()

        # Initialize the integrator attributes
        self.min_threshold = min_threshold
        self.min_threshold_applied = min_threshold_applied
        self.max_threshold = max_threshold
        self.max_threshold_applied = max_threshold_applied
        


    def integrate(self, p_data, inclusion_mask, no_data_mask=None,
            exclude_above_line=None, exclude_below_line=None):
        """
        integrate ...
        """


        # key concepts
        # cell_thickness - effective height of cell excluding samples that are excluded by the cell mask
        # no_data - data flagged as nan in the Sv grid these are to be completely excluded (essentially bad data)
        # 


        # Now that we have the grid, we can use it to extract the data
        # interval by layer.
        for interval in range(integration_grid.n_intervals):

            for layer in range(integration_grid.n_layers):

                # get a mask that we can use to return sample data for this cell.
                cell_mask = integration_grid.get_cell_mask(interval, layer)

                # use the mask to get the cell data
                cell_Sv = Sv_data[cell_mask]

                # and again to get the included data mask for this cell
                cell_include = inclusion_mask[cell_mask]

                #  now get some info our our cell and cell sample data
                no_data_samples = np.isnan(cell_Sv)
                n_no_data_samples = np.count_nonzero(no_data_samples)
                n_included_samples = np.count_nonzero(cell_include)
                n_excluded_samples = np.count_nonzero(~cell_include)
                n_pings_in_cell  = integration_grid.interval_pings[interval] # rick had switched pings and samples
                n_samples = integration_grid.layer_samples[layer] # rick had switched pings and samples
                n_total_samples = n_samples * n_pings_in_cell
                
                # compute effective height of layer by calculatin the fraction of the cell that has been excluded
                # and pro-rating the height.  Bad data are excluded from the total number of samples
                # this is the same concept as Echoview's layer_height
                cell_thickness=layer_thickness * ( n_included_samples /(n_total_samples- n_no_data_samples))  
                
                
                # Alex added this line as need to compute Sv where we have data
                cell_sv_included=cell_Sv[cell_include]  # map out the cells to include
                
                #  for examples sake - compute the cell mean Sv and mean of sv.
                if np.nansum(cell_sv_included) > 0:
                    
                    cell_mean_sv = np.nanmean(cell_sv_included) # linear form of volume backscatter (m^-1 or m^2/m^3)
                    cell_mean_Sv = 10.0 * np.log10(cell_mean_sv) # log form of volume backscatter (dB re 1 m^-1)
                    cell_nasc = cell_mean_sv* cell_thickness * 4 * np.pi * 1852**2
           
                # if no data in cell, make it a nan
                elif  cell_sv_included.size==0:
                    cell_mean_sv = np.nan # linear form of volume backscatter (m^-1 or m^2/m^3)
                    cell_mean_Sv = np.nan # log form of volume backscatter (dB re 1 m^-1)
                    cell_nasc =  np.nan
                
                else: # if any samples present report as zero
                    cell_mean_Sv = -999
                    cell_mean_sv = 0
                    cell_nasc= 0

                #  and print out the info
                print("Interval %i, Layer %i" % (interval, layer))
                print("      total samples: %i" % (n_total_samples))
                print(" n included samples: %i" % (n_included_samples))
                print(" n excluded samples: %i" % (n_excluded_samples))
                print("    no_data samples: %i" % (n_no_data_samples))
                print("            mean Sv: %3.2f" % (cell_mean_Sv))
                print("            cell_thickness: %3.2f" % (cell_thickness))
                print("            cell_nasc: %3.2f" % (cell_nasc))
                print("            n_pings: %3.2f" % (n_pings_in_cell))


    def __str__(self):
        """Re-implements string method to provide basic information.

        Reimplemented string method that provides some basic info about the
        grid object.

        Return:
            A message with basic information about the grid object.
        """

        # Print the class and address.
        msg = "{0} at {1}\n".format(str(self.__class__), str(hex(id(self))))

        # Print some other basic information.
        msg = "{0}                 grid name: {1}\n".format(msg, self.name)
        msg = "{0}           horizontal axis: {1}\n".format(msg, self.interval_axis)
        msg = "{0}           interval length: {1}\n".format(msg, str(self.interval_length))
        msg = "{0}               n intervals: {1}\n".format(msg, self.n_intervals)
        msg = "{0}                layer axis: {1}\n".format(msg, self.layer_axis)
        msg = "{0}           layer thickness: {1}\n".format(msg, self.layer_thickness)
        msg = "{0}                  n layers: {1}\n".format(msg, self.n_layers)

        return msg
