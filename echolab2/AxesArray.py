# coding=utf-8
'''
.. :module:: echolab.AxesArray
    :synopsis: Contains the AxesArray, a subclass of numpy.ma.masked_array


| Zac Berkowitz <zachary.berkowitz@noaa.gov>
| National Oceanic and Atmospheric Administration
| Alaska Fisheries Science Center
| Midwater Assesment and Conservation Engineering Group
'''

import numpy as np
import logging

__all__ = ['AxesArray']
log = logging.getLogger(__name__)

def ma_method_wrapper(ma_func):
    '''
    Wrapper for methods of the MaskedArray class that can
    operate along a specified dimension (mean, min, var, etc.)
    
    Used as a decorator in the AxesArray class object, 
    see AxesArray.var
    '''
    #Get the name of the method we're wrapping
    ma_method = getattr(np.ma.MaskedArray, ma_func.__name__)
    
    #Actual function that does the work:
    def wrapped(self, *args, **kwargs):
        
        #Create a MaskedArray view of the AxesArray instance data &
        #apply the method  
        ma_view = self.view(type=np.ma.MaskedArray)
        result = ma_method(ma_view, *args, **kwargs)
        
        #If the result is a scalar, return immediately.  We don't need
        #to add any info
        if np.isscalar(result):
            return result
        
        #Some things are done in place, so return None if result is None
        elif result is None:
            return None
        
        #Otherwise, transform the result back into an AxesArray instance
        result = result.view(type(self))
        
        #Update the meta information (including axes) from the original
        result._update_from(self)
        
        #Overwrite axes information w/ copies of non-singleton dimensions from
        #original
        
        axes_to_copy = list(range(self.ndim))
        axes_to_ignore = kwargs.get('axis', None)
        
        if axes_to_ignore is not None:
            axes_to_copy.remove(axes_to_ignore)
        
        result.axes = [x.copy() for (dim, x) in enumerate(self.axes) if dim in axes_to_copy]           
        
        return result
    
    #Set this method's docstring and name to the original MaskedArray.ma_method's
    wrapped.__doc__ = ma_method.__doc__
    wrapped.__name__ = ma_method.__name__
    
    return wrapped

class AxesArray(np.ma.masked_array):
    '''
    A MaskedArray subclass with additional axes information

    attributes:
        info         dict of additional information
        axes         list of np.ndarrays with axes values for each dimension

    see :class:`numpy.ma.masked_array` for more info on masked arrays.
    '''
    
    __array_priority__ = 20

    def __new__(cls, input_array, axes=None, copy=False,
                info=None):

      
        if isinstance(input_array, (np.ma.masked_array, np.ndarray)):
            obj = np.ma.masked_array(input_array, copy=copy).view(cls)

        else:
            obj = np.ma.masked_array(np.array(input_array, copy=copy), copy=False).view(cls)

        if axes is not None:
            obj.axes = axes
                     
        if info is not None:
            obj.info = info
        
        return obj

    @property
    def axes(self):
        return self._optinfo.get('axes', None)
    
    @axes.setter
    def axes(self, axes):
        self._optinfo['axes'] = axes

    @property 
    def info(self):
        return self._optinfo.get('info', None)

    @info.setter
    def info(self, info):
        self._optinfo['info'] = info

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def __getitem__(self, indx):
        _data = np.ndarray.view(self, type=np.ma.masked_array)
        _axes  = self.axes

        #Get the data items
        ma_out = np.ma.masked_array.__getitem__(_data, indx)

        #Return scalar values immediately
        if not isinstance(ma_out, np.ma.masked_array):
            return ma_out

        #Intialize axes list
        new_axes = []
        
        #Slicing Record arrays..
        if isinstance(indx, str):
            for dim in range(_data.ndim):
                new_axes.append(_axes[dim])
                
        #When we slice by rows, i.e. PingArray[0] or PingArray[0:3]
        elif np.isscalar(indx) or isinstance(indx, (slice, np.ndarray)):
            new_axes.append(_axes[0][indx])


            #retain all column axes values
            for dim in range(1, _data.ndim):
                new_axes.append(_axes[dim])

        #When we slice by columns, PingArray[0, :], PingArray[:, 0], PingArray[:, 0:3], etc.
        else:
            for dim, dim_slice in enumerate(indx):
                #a slice can be None if we're reshaping a single row->col
                #vector (or col->row).  i.e. casting
                #a_new = a[:, None] (this is done for 1-D vectors in
                #matplotlib's plot command.
                if dim_slice is None:
                    new_axes.append(np.array([None]))
                else:
                    new_axes.append(_axes[dim][dim_slice])

        #Recast as an AxesArray
        dout = ma_out.view(type(self))
        
        #Store new axes
        dout.axes = new_axes

        return dout

    
    def __array_finalize__(self, obj):
        np.ma.masked_array.__array_finalize__(self, obj)

        #Defaults
        self.info = getattr(obj, 'info', {})
        axes = getattr(obj, 'axes', None)        
        if axes is None:
            self.axes = []
            for dim_len in obj.shape:
                self.axes.append(np.arange(dim_len))
        else:
            self.axes = [x.copy() for x in axes]

        self._mask=self._mask.copy()

    def copy(self):       
        new = np.ma.masked_array.copy(self)
        new.axes = [np.copy(x) for x in new.axes]
        new.info = new.info.copy()    
        return new
    
#    def mean(self, axis=None, dtype=None, out=None):
#        
#        if axis is None:
#            return np.ma.MaskedArray.mean(self, axis=axis, dtype=dtype, out=out)
#        else:
#            mean_array = np.ma.MaskedArray.mean(self, axis=axis, dtype=dtype, out=out).astype(type(self))
#            mean_array.axes = [x.copy() for x in self.axes if len(x) in mean_array.shape]            
#            return mean_array
#        
#    mean.__doc__ = np.ma.MaskedArray.mean.__doc__

    @ma_method_wrapper
    def mean(self, axis=None, dtype=None, out=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass        

    @ma_method_wrapper
    def var(self, axis=None, dtype=None, out=None, ddof=0):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass
    
    @ma_method_wrapper
    def min(self, axis=None, out=None, fill_value=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass        

    @ma_method_wrapper
    def mini(self, axis=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass    
        
    @ma_method_wrapper
    def max(self, axis=None, out=None, fill_value=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass
    
    @ma_method_wrapper
    def std(self, axis=None, dtype=None, out=None, ddof=0):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass
    
    @ma_method_wrapper
    def sort(self, axis= -1, kind='quicksort', order=None,
             endwith=True, fill_value=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass
        
#    def sort(self, axis= -1, kind='quicksort', order=None,
#             endwith=True, fill_value=None):
#        '''
#        Block in-place sort calls.  We do not handle sorting the .axes
#        meta-information
#        '''
#        raise NotImplementedError('Sorting in place is undefiend for AxesArray objects')     

    @ma_method_wrapper
    def ptp(self, axis=None, out=None, fill_value=None):
        '''
        This docstring is ignored, it is replaced by the original
        MaskedArray method docstring in the ma_method_wrapper definition.
        
        This method definition should be empty.  All work is done by 
        the decorator.
        '''
        pass