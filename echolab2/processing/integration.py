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
|   Alex DeRobertis   <alex.derobertis@noaa.gov>
|
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import csv
import numpy as np
from ..processing import mask


class results(object):


    """results
    

    """

    def __init__(self, grid):
        """Initializes a new integration.results class object. Results objects contain
        the results from an integration operation applied to the provided grid. The class
        stores the results and associated data in numpy arrays (n_intervals x nLayers) in
        size in the following attributes:

            mean_Sv
            nasc
            min_Sv
            max_Sv
            n_no_data_samples
            n_included_samples
            n_excluded_samples
            n_total_samples
            
        Individual cell results are extracted by indexing these arrays by grid interval and
        grid cell. The indexes are zero based and cell 0 with index [0,0] is in the upper
        left corner of the grid.

    Arguments:

        grid (pyecholab.processing.grid): A reference to the grid used to generate these results.

        """
        super(results, self).__init__()

        self._iter_interval = 0
        self._iter_layer = 0
        
        self.grid = grid

        self.mean_Sv = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.nasc = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.min_Sv = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.max_Sv = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.n_no_data_samples = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.n_included_samples = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.n_excluded_samples = np.full((grid.n_intervals, grid.n_layers), np.nan)
        self.n_total_samples = np.full((grid.n_intervals, grid.n_layers), np.nan)


    def export_to_csv(self, filename, output_empty_cells=False):
        
        #  get a list containing the headers for the file
        file_headers = self._get_csv_headers()
        
        try:
            # open the file
            f = open(filename, 'w')

            # create the csv writer and write the header
            writer = csv.DictWriter(f, fieldnames=file_headers)
            writer.writeheader()
            
            # then write the rows
            for cell_data in self:
                if np.isfinite(cell_data['nasc']) or output_empty_cells:
                    writer.writerow(cell_data)
            
            # close the file
            f.close()
            
        except Exception as e:
            raise e
    
    
    def __iter__(self):
        """
        The integration.results class is iterable and will return results by interval, row
        """
        
        self._iter_interval = 0
        self._iter_layer = 0
        
        return self

    def __next__(self):

        #  check if we are at the bottom layer and need to advance to the next interval
        if self._iter_layer == self.grid.n_layers:
            self._iter_layer = 0
            self._iter_interval += 1
        
        #  check if we're done with the last interval
        if self._iter_interval == self.grid.n_intervals:
            raise StopIteration

        #  build the return dict for this cell's results
        cell_data = {}
        
        #  first populate the results for this cell
        cell_data['interval'] = self._iter_interval + 1
        cell_data['layer'] = self._iter_layer + 1
        cell_data['nasc'] = self.nasc[self._iter_interval, self._iter_layer]
        cell_data['min_Sv'] = self.min_Sv[self._iter_interval, self._iter_layer]
        cell_data['mean_Sv'] = self.mean_Sv[self._iter_interval, self._iter_layer]
        cell_data['max_Sv'] = self.max_Sv[self._iter_interval, self._iter_layer]
        cell_data['n_no_data_samples'] = self.n_no_data_samples[self._iter_interval, self._iter_layer]
        cell_data['n_included_samples'] = self.n_included_samples[self._iter_interval, self._iter_layer]
        cell_data['n_excluded_samples'] = self.n_excluded_samples[self._iter_interval, self._iter_layer]
        cell_data['n_total_samples'] = self.n_total_samples[self._iter_interval, self._iter_layer]
        
        #  then add the grid properties for this cell
        if hasattr(self.grid, 'layer_range_start'):
            cell_data['layer_range_start'] = self.grid.layer_range_start[self._iter_layer]
            cell_data['layer_range_middle'] = self.grid.layer_range_middle[self._iter_layer]
            cell_data['layer_range_end'] = self.grid.layer_range_end[self._iter_layer]
        else:
            cell_data['layer_depth_start'] = self.grid.layer_depth_start[self._iter_layer]
            cell_data['layer_depth_middle'] = self.grid.layer_depth_middle[self._iter_layer]
            cell_data['layer_depth_end'] = self.grid.layer_depth_end[self._iter_layer]
        cell_data['interval_ping_start'] = self.grid.interval_ping_start[self._iter_interval]
        cell_data['interval_ping_middle'] = self.grid.interval_ping_middle[self._iter_interval]
        cell_data['interval_ping_end'] = self.grid.interval_ping_end[self._iter_interval]
        cell_data['interval_time_start'] = self.grid.interval_time_start[self._iter_interval]
        cell_data['interval_time_middle'] = self.grid.interval_time_middle[self._iter_interval]
        cell_data['interval_time_end'] = self.grid.interval_time_end[self._iter_interval]
        
        #  add the optional grid params
        if hasattr(self.grid, 'interval_lat_start'):
            cell_data['interval_lat_start'] = self.grid.interval_lat_start[self._iter_interval]
            cell_data['interval_lat_middle'] = self.grid.interval_lat_middle[self._iter_interval]
            cell_data['interval_lat_end'] = self.grid.interval_lat_end[self._iter_interval]
        if hasattr(self.grid, 'interval_lon_start'):
            cell_data['interval_lon_start'] = self.grid.interval_lon_start[self._iter_interval]
            cell_data['interval_lon_middle'] = self.grid.interval_lon_middle[self._iter_interval]
            cell_data['interval_lon_end'] = self.grid.interval_lon_end[self._iter_interval]
        if hasattr(self.grid, 'interval_mean_sog'):
            cell_data['interval_mean_sog'] = self.grid.interval_mean_sog[self._iter_interval]
        if hasattr(self.grid, 'interval_trip_distance_nmi_start'):
            cell_data['interval_trip_distance_nmi_start'] = self.grid.interval_trip_distance_nmi_start[self._iter_interval]
            cell_data['interval_trip_distance_nmi_middle'] = self.grid.interval_trip_distance_nmi_middle[self._iter_interval]
            cell_data['interval_trip_distance_nmi_end'] = self.grid.interval_trip_distance_nmi_end[self._iter_interval]

        #  increment the layer counter
        self._iter_layer += 1
        
        return cell_data


    def _get_csv_headers(self):
        """
        _get_csv_headers is an internal method that returns a list defining the CSV file
        headers for the current results. The order items are in this list defines the
        order they are written in the CSV.
        """
        # add the reults and interval attributes
        csv_headers = ['interval', 'layer','nasc','min_Sv','mean_Sv','max_Sv',
                'n_no_data_samples','n_included_samples','n_excluded_samples',
                'n_total_samples', 'interval_ping_start', 'interval_ping_middle',
                'interval_ping_end','interval_time_start','interval_time_middle',
                'interval_time_end'] 

        #  add the layer attributes
        if hasattr(self.grid, 'layer_range_start'):
            csv_headers.extend(['layer_range_start','layer_range_middle',
                    'layer_range_end'])
        else:
            csv_headers.extend(['layer_depth_start','layer_depth_middle',
                    'layer_depth_end'])

        #  add the optional grid attributes
        if hasattr(self.grid, 'interval_lat_start'):
            csv_headers.extend(['interval_lat_start','interval_lat_middle',
                    'interval_lat_end'])
        if hasattr(self.grid, 'interval_lon_start'):
            csv_headers.extend(['interval_lon_start','interval_lon_middle',
                    'interval_lon_end'])
        if hasattr(self.grid, 'interval_mean_sog'):
            csv_headers.extend(['interval_mean_sog'])
        if hasattr(self.grid, 'interval_trip_distance_nmi_start'):
            csv_headers.extend(['interval_trip_distance_nmi_start',
                    'interval_trip_distance_nmi_middle','interval_trip_distance_nmi_end'])
            
        return csv_headers


    def __str__(self):
        """Re-implements string method to provide basic information.

        Reimplemented string method that provides some basic info about the
        integration.results object.

        Return:
            A message with basic information about the integration.results object.
        """

        # Print the class and address.
        msg = "{0} at {1}\n".format(str(self.__class__), str(hex(id(self))))

        # Print some other basic information.
        msg = "{0}       Integration results: {1} intervals by {2} layers\n".format(msg,
                self.grid.n_intervals, self.grid.n_layers)
        msg = "{0}      grid horizontal axis: {1}\n".format(msg, self.grid.interval_axis)
        msg = "{0}      first interval start: {1}\n".format(msg, str(self.grid.interval_time_start[0]))
        msg = "{0}         last interval end: {1}\n".format(msg, str(self.grid.interval_time_end[-1]))


        return msg



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
        


    def integrate(self, p_data, integration_grid, inclusion_mask=None, no_data_mask=None,
            exclude_above_line=None, exclude_below_line=None):
        """
        integrate ...
        """

        # Generate the threshold mask if we're supposed to . It is assumed that
        # the specified thresholds are in the same units as the provided data.
        threshold_mask = None
        if self.min_threshold_applied and self.max_threshold_applied:
            # apply both min and max thresholds
            max_threshold_mask = p_data.data > self.max_threshold
            min_threshold_mask = p_data.data < self.min_threshold
            # now OR them for the final threshold mask
            threshold_mask = max_threshold_mask | min_threshold_mask
        elif self.min_threshold_applied:
            # we're only applying the min threshold
            threshold_mask = p_data.data < self.min_threshold
        elif self.max_threshold_applied:
            # we're only applying the max threshold
            threshold_mask = p_data.data > self.max_threshold
        
        # check if we have been given an inclusion mask and create if not.
        # By default we assume all samples will be included in integration.
        if inclusion_mask is None:
            inclusion_mask = mask.mask(like=p_data, value=True)
            
        # apply exclude above and below lines if provided
        if exclude_above_line is not None:
            inclusion_mask.apply_above_line(exclude_above_line, value=False)
        if exclude_below_line is not None:
            inclusion_mask.apply_below_line(exclude_below_line, value=False)
        
        #  create the results object to return
        int_results = results(integration_grid)
        
        # convert log data to linear
        if p_data.is_log:
            p_data.to_linear()
            p_data_is_log = True
        else:
            p_data_is_log = False
        
        # using the provided grid, integrate by interval and layer
        for interval in range(integration_grid.n_intervals):
            for layer in range(integration_grid.n_layers):

                # get a mask that we can use to return sample data for this cell.
                cell_mask = integration_grid.get_cell_mask(interval, layer)

                # use the mask to get the cell data
                cell_data = p_data[cell_mask]

                # and again to get the included data mask for this cell
                cell_include = inclusion_mask[cell_mask]
                
                # check if the user provided a no data mask and apply
                if no_data_mask is not None:
                    # yes, get the no data samples and set to nan
                    cell_bad = no_data_mask[cell_mask]
                    cell_data[cell_bad] = np.nan 
                
                #  apply the threshold mask if specified
                if threshold_mask is not None:
                    # When applying threshold masks for integration, you want the samples
                    # to be included in the layer thickness calculation so we will just 
                    # set these samples to a tiny number
                    cell_zero = threshold_mask[cell_mask]
                    if p_data.is_log:
                        cell_data[cell_zero] = -999
                    else:
                        cell_data[cell_zero] = 1e-100

                # now get some info our our cell and cell sample data
                no_data_samples = np.isnan(cell_data)
                n_no_data_samples = np.count_nonzero(no_data_samples)
                n_included_samples = np.count_nonzero(cell_include)
                n_excluded_samples = np.count_nonzero(~cell_include)
                n_pings_in_cell  = integration_grid.interval_pings[interval]
                n_samples = integration_grid.layer_samples[layer]
                n_total_samples = n_samples * n_pings_in_cell
                
                # compute effective height of layer by calculating the fraction of the cell
                # that has been excluded and pro-rating the height.  Bad data are excluded
                # from the total number of samples.
                cell_thickness = integration_grid.layer_thickness * (n_included_samples / 
                        (n_total_samples - n_no_data_samples))  
                
                # get the data we're integrating
                cell_data_included = cell_data[cell_include]
                
                #  Now compute the mean and some other bits
                if np.nansum(cell_data_included) > 0:
                    cell_mean_sv = np.nanmean(cell_data_included)
                    cell_min_sv = np.nanmin(cell_data_included)
                    cell_max_sv = np.nanmax(cell_data_included)
                    if cell_mean_sv > 1e-100:
                        cell_mean_Sv = 10.0 * np.log10(cell_mean_sv)
                        cell_max_Sv = 10.0 * np.log10(cell_max_sv)
                        cell_nasc = cell_mean_sv * cell_thickness * 4 * np.pi * 1852**2
                    else:
                        cell_mean_Sv = -999
                        cell_max_Sv = -999
                        cell_nasc= 0
                    if cell_min_sv > 1e-100:
                        cell_min_Sv = 10.0 * np.log10(cell_min_sv)
                    else:
                        cell_min_Sv = -999
           
                # if no data in cell, make it a nan
                elif cell_data_included.size == 0:
                    cell_mean_Sv = np.nan
                    cell_min_Sv = np.nan
                    cell_max_Sv = np.nan
                    cell_nasc = np.nan
                
                else: # if any samples present report as zero
                    cell_mean_Sv = -999
                    cell_min_Sv = -999
                    cell_max_Sv = -999
                    cell_nasc= 0

                #  insert the results into the results object
                int_results.mean_Sv[interval, layer] = cell_mean_Sv
                int_results.nasc[interval, layer] = cell_nasc
                int_results.min_Sv[interval, layer] = cell_min_Sv
                int_results.max_Sv[interval, layer] =cell_max_Sv
                int_results.n_no_data_samples[interval, layer] = n_no_data_samples
                int_results.n_included_samples[interval, layer] = n_included_samples
                int_results.n_excluded_samples[interval, layer] = n_excluded_samples
                int_results.n_total_samples[interval, layer] = n_total_samples
        
        #  convert back to log if required
        if p_data_is_log:
            p_data.to_log()
        
        return int_results


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
