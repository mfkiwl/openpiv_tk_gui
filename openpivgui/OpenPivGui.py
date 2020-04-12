#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''A simple GUI for OpenPIV.'''

__version__ = '0.1.7'

__licence__ = '''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

__email__= 'vennemann@fh-muenster.de'

import os
import re
import sys
import json
import inspect
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from datetime import datetime

import numpy as np
import openpiv.tools as piv_tls
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure as Fig

from openpivgui.OpenPivParams import OpenPivParams
from openpivgui.CreateToolTip import CreateToolTip
from openpivgui.MultiProcessing import MultiProcessing
from openpivgui.PostProcessing import PostProcessing

from openpivgui.open_piv_gui_tools import str2list, str2dict, get_dim


class OpenPivGui(tk.Tk):
    '''Simple OpenPIV GUI

    Usage:

    1. Press »select files for processing« and choose
    some images. Use Ctrl + Shift for selecting mutliple files.

    2. Click on the links in the file-list to inspect the images.

    3. Walk through the tabs, select the desired functions,
    and edit the corresponding parameters.

    4. Press »start processing chain« to start the processing.

    5. Inspect the results by clicking on the links in the file-list.

    6. Use the »back« and »forward« buttons to inspect
    intermediate results.

    4. Use »dump settings« to document your project. You can recall them
    anytime by pressing »load settings«. The lab-book entries
    are also restored from the settings file.

    See also:

    https://git.fh-muenster.de/pv238554/openpivgui
    '''

    def __init__(self):
        '''Standard initialization method.'''
        self.VERSION = __version__
        self.TITLE = 'Simple OpenPIV GUI'
        tk.Tk.__init__(self)
        self.title(self.TITLE + ' ' + self.VERSION)
        self.p = OpenPivParams()
        self.p.load_settings(self.p.params_fname)
        # background variable for widget data
        self.tkvars = {}
        self.__init_widgets()
        self.set_settings()
        self.log(timestamp=True, text='OpenPIV session started.')
        self.log(text = 'OpenPivGui version: ' + self.VERSION)

    def start_processing(self):
        '''Start the processing chain.
        
        This is the place to implement additional function calls.
        '''
        self.get_settings()
        if self.p['extd_search_area']:
            # parallel PIV evaluation:
            mp = MultiProcessing(self.p)
            return_fnames = mp.get_save_fnames()
            if "idlelib" in sys.modules:
                self.log('Running as a child of IDLE: ' +
                         'Deactivate multiprocessing.')
                cpu_count = 1
            else:
                cpu_count = os.cpu_count()
            mp.run(func=mp.process, n_cpus=cpu_count)
            # update file list with result vector files:
            self.tkvars['fnames'].set(return_fnames)
            self.log(timestamp=True,
                     text='\nPIV evaluation finished.',
                     group=self.p.PIVPROC)
        self.get_settings()
        if self.p['sig2noise']:
            # validation
            self.tkvars['fnames'].set(
                PostProcessing(self.p).sig2noise())
            self.log(timestamp=True,
                     text='\nValidation finished.',
                     group=self.p.VALIDATION)
        self.get_settings()
        if self.p['repl']:
            # post processing
            self.tkvars['fnames'].set(
                PostProcessing(self.p).repl_outliers())
            self.log(timestamp=True,
                     text='\nPost processing finished.',
                     group=self.p.POSTPROC)

    def __init_widgets(self):
        '''Creates a widget for each variable in a parameter object.'''
        # plotting area:
        self.__init_fig_canvas()
        # parameter area:
        self.__init_notebook()
        # buttons:
        self.__init_buttons()
        # variable widgets:
        for key in sorted(self.p.index, key=self.p.index.get):
            if self.p.type[key] == 'bool':
                self.__init_checkbutton(key)
            elif self.p.type[key] == 'str[]':
                self.__init_listbox(key)
            elif self.p.type[key] == 'text':
                self.__init_text_area(key)
            elif self.p.type[key] is None:
                self.__add_tab(key)
            else:
                self.__init_entry(key)

    def __init_fig_canvas(self):
        '''Creates a plotting area for matplotlib.'''
        self.fig = Fig()
        f = ttk.Frame(self)
        f.pack(side='left',
               fill='both',
               expand='True')
        self.fig_canvas = FigureCanvasTkAgg(
            self.fig, master=f)
        self.fig_canvas.draw()
        self.fig_canvas.get_tk_widget().pack(
            side='left',
            fill='x',
            expand='True')
        self.fig_toolbar = NavigationToolbar2Tk(
            self.fig_canvas, f)
        self.fig_toolbar.update()
        self.fig_canvas._tkcanvas.pack(side='top',
                                       fill='both',
                                       expand='True')
        self.fig_canvas.mpl_connect(
            "key_press_event",
            self.__fig_toolbar_key_pressed)

    def __fig_toolbar_key_pressed(self, event):
        '''Handles matplotlib toolbar events.'''
        key_press_handler(event,
                          self.fig_canvas,
                          self.fig_toolbar)

    def __init_notebook(self):
        '''The notebook is the root widget for tabs or riders.'''
        self.nb = ttk.Notebook()

    def __add_tab(self, key):
        '''Add an additional rider to the notebook.'''
        self.set_frame = ttk.Frame(self.nb)
        self.nb.add(self.set_frame, text=self.p.label[key])
        self.nb.pack(side='left',
                     fill='both',
                     expand='True')

    def __init_buttons(self):
        '''Add buttons and bind them to methods.'''
        f = ttk.Frame(self)
        ttk.Button(f,
                   text='select files for processing',
                   command=self.select_image_files).pack(fill='x')
        ttk.Button(f,
                   text='start processing chain',
                   command=self.start_processing).pack(fill='x')
        ttk.Button(f,
                   text='dump settings',
                   command=lambda: self.p.dump_settings(
                       filedialog.asksaveasfilename())).pack(fill='x')
        ttk.Button(f,
                   text='load settings',
                   command=self.load_settings).pack(fill='x')
        ttk.Button(f,
                   text='delete files',
                   command=self.delete_files).pack(fill='x')
        ttk.Button(f,
                   text='user function',
                   command=self.user_function).pack(fill='x')
        ttk.Button(f,
                   text='help',
                   command=lambda: messagebox.showinfo(
                       title='Help',
                       message=inspect.cleandoc(
                           OpenPivGui.__doc__))).pack(fill='x')
        f.pack(side='left', fill='x')
    
    def user_function(self):
        '''Example function. Extend the code here.'''
        messagebox.showinfo(
            title='User Function',
            message='Replace this by something useful.')
        

    def delete_files(self):
        '''Delete files currently listed in the file list.'''
        files = self.p['fnames'][:]
        for f in files:
            os.remove(f)
        self.navigate('back')

    def load_settings(self):
        '''Load settings from a JSON file.'''
        self.p.load_settings(filedialog.askopenfilename())
        self.set_settings()

    def __init_listbox(self, key):
        '''Creates an interactive list of filenames.

        Args:
            key (str): Key of a settings object of type str[].
        '''
        # root widget
        f = ttk.Frame(self)
        f.pack(side='left',
               fill='both',
               expand='True')
        # scrolling
        sb = ttk.Scrollbar(f, orient="vertical")
        sb.pack(side='right', fill='y')
        lb = tk.Listbox(f, yscrollcommand=sb.set)
        lb['height'] = 25
        sb.config(command=lb.yview)
        # background variable
        self.tkvars.update({key: tk.StringVar()})
        self.tkvars[key].set(self.p['fnames'])
        lb['listvariable'] = self.tkvars[key]
        # interaction
        lb.bind('<<ListboxSelect>>', self.__listbox_selection_changed)
        lb.pack(side='top', fill='both', expand='True')
        # navigation buttons
        f = ttk.Frame(f)
        ttk.Button(f,
                   text='< back',
                   command=lambda : self.navigate('back')).pack(
                   side='left', fill='x')
        ttk.Button(f,
                   text='forward >',
                   command=lambda : self.navigate('forward')).pack(
                   side='right', fill='x')
        f.pack()

    def navigate(self, direction):
        '''Navigate through processing steps.

        Args:
            direction (str): »back« or »forward«.

        Display a filtered list of files of the current
        directory. This function cycles through the filters
        specified by the key 'navi_pattern' in the settings object.
        '''        
        pattern_lst = str2list(self.p['navi_pattern'])
        dirname = os.path.dirname(self.p['fnames'][0])
        files = os.listdir(dirname)
        if direction == 'back':
            self.p.navi_position -= 1
            if self.p.navi_position == -1:
                self.p.navi_position = len(pattern_lst)-1
        elif direction == 'forward':
            self.p.navi_position += 1
            if self.p.navi_position == len(pattern_lst):
                self.p.navi_position = 0
        filtered = (self.file_filter(
                    files,
                    pattern_lst[self.p.navi_position]))
        if filtered != []:
            filtered = [dirname + os.sep + f for f in filtered]
            filtered.sort()
            self.tkvars['fnames'].set(filtered)
            self.get_settings()
        # try next filter, if result is empty
        else: self.navigate(direction)

    def file_filter(self, files, pattern):
        '''Filter a list of files to  match a pattern.

        Args:
            files (str[]): A list of pathnames.
            pattern (str): A regular expression for filtering the list.

        Returns:
            str[]: List items that match pattern.
        '''
        filtered = []
        print('file filter: ' + pattern)
        p = re.compile(pattern)
        for f in files:
            if p.search(f):
                filtered.append(f);
        return(filtered)

    def __init_text_area(self, key):
        '''Init a text area, here used as a lab-book, for example.
        
        The content is saved automatically to the parameter object,
        when the mouse leaves the text area.'''
        self.ta = tk.Text(self.set_frame)
        self.ta.pack()
        self.ta.bind('<Leave>',
                     (lambda _: self.__get_text(key)))
        ttk.Button(self.set_frame,
                   text='clear',
                   command=lambda: self.ta.delete(
                       '1.0',
                       tk.END)).pack(fill='x')

    def __get_text(self, key):
        '''Get text from lab-book and copy it to parameter object.'''
        self.p[key] = self.ta.get('1.0', tk.END)

    def __listbox_selection_changed(self, event):
        '''Handles selection change events of the file listbox.'''
        try:
            index = event.widget.curselection()[0]
        except IndexError:
            pass  # nothing selected
        else:
            self.get_settings()
            self.show(self.p['fnames'][index])

    def __init_entry(self, key):
        '''Creates a label and an entry in a frame.

        A corresponding tk background textvariable is also crated. An 
        option menu is created instead of en entry, if a hint is given
        in the parameter object. The help string in the parameter object
        is used for creating a tooltip.

        Args:
            key (str): Key of a parameter obj.
        '''
        f = ttk.Frame(self.set_frame)
        f.pack(fill='x')
        l = ttk.Label(f, text=self.p.label[key])
        CreateToolTip(l, self.p.help[key])
        l.pack(side='left')
        if self.p.type[key] == 'int':
            self.tkvars.update({key: tk.IntVar()})
        elif self.p.type[key] == 'float':
            self.tkvars.update({key: tk.DoubleVar()})
        else:
            self.tkvars.update({key: tk.StringVar()})
        if self.p.hint[key] is not None:
            e = tk.OptionMenu(f,
                              self.tkvars[key],
                              *self.p.hint[key])
        else:
            e = ttk.Entry(f)
            e['textvariable'] = self.tkvars[key]
        CreateToolTip(e, self.p.help[key])
        e.pack(side='right')

    def __init_checkbutton(self, key):
        '''Create a checkbutton with label and tooltip.'''
        f = ttk.Frame(self.set_frame)
        f.pack(fill='x')
        self.tkvars.update({key: tk.BooleanVar()})
        self.tkvars[key].set(bool(self.p[key]))
        cb = ttk.Checkbutton(f)
        cb['variable'] = self.tkvars[key]
        cb['onvalue'] = True
        cb['offvalue'] = False
        cb['text'] = self.p.label[key]
        CreateToolTip(cb, self.p.help[key])
        cb.pack(side='left')

    def log(self, timestamp=False, text=None, group=None):
        ''' Add an entry in the lab-book.

        Kwargs:
            timestamp (bool): Print current time.
                              Pattern: yyyy-mm-dd hh:mm:ss.
                              (default False)
            text (str): Print a text, a linebreak is appended. 
                        (default None)
            group (int): Print group of parameters.
                         (e.g. OpenPivParams.PIVPROC)

        Example:
            log(text='processing parameters:', 
                group=OpenPivParams.POSTPROC)
        '''
        if text is not None:
            self.ta.insert(tk.END, text + '\n')
        if timestamp:
            td = datetime.today()
            s = '-'.join((str(td.year), str(td.month), str(td.day))) + \
                ' ' + \
                ':'.join((str(td.hour), str(td.minute), str(td.second)))
            self.log(text=s)
        if group is not None:
            self.log(text='Parameters:')
            for key in self.p.param:
                if group < self.p.index[key] < group+1000:
                    s = key + ': ' + str(self.p[key])
                    self.log(text=s)

    def get_settings(self):
        '''Copy widget variables to the parameter object.'''
        for key in self.tkvars:
            if self.p.type[key] == 'str[]':
                self.p[key] = str2list(self.tkvars[key].get())
            else:
                self.p[key] = self.tkvars[key].get()

    def set_settings(self):
        '''Copy values of the parameter object to widget variables.'''
        for key in self.tkvars:
            self.tkvars[key].set(self.p[key])
        self.ta.insert('1.0', self.p['lab_book_content'])

    def select_image_files(self):
        '''Show a file dialog to select one or more filenames.'''
        print('Use Ctrl + Shift to select multiple files.')
        files = filedialog.askopenfilenames(multiple=True)
        self.p['fnames'] = list(files)
        self.tkvars['fnames'].set(self.p['fnames'])

    def show(self, fname):
        '''Display a file.

        This method distinguishes vector data (file extensions
        txt, dat, jvc and vec) and images (all other file extensions).

        Args:
            fname (str): A filename.
        '''
        ext = fname.split('.')[-1]
        if ext in ['txt', 'dat', 'jvc', 'vec']:
            if self.p['plot_type'] == 'histogram':
                self.show_histogram(
                    fname,
                    quantity=self.p['histogram_quantity'],
                    bins=self.p['histogram_bins'],
                    log_scale=self.p['histrogram_log_scale'])
            elif self.p['plot_type'] == 'profiles':
                self.show_profiles(
                    fname,
                    orientation=self.p['profiles_orientation'])
            elif self.p['plot_type'] == 'scatter':
                self.show_scatter(fname)
            else:
                self.show_vec(
                    fname,
                    scale=self.p['vec_scale'],
                    width=self.p['vec_width'])
        else:
            self.show_img(fname)

    def show_histogram(self, fname, quantity, bins, log_scale, **kw):
        '''Plot an histogram.

        Plots an histogram of the specified quantity.

        Args:
            fname (str): A filename containing vector data.
            quantity (str): Either v (abs v), 
                                   v_x (x-component) or 
                                   v_y (y-component).
            bins (int): Number of bins (bars) in the histogram.
            log_scale (boolean): Use logaritmic vertical axis.
            **kw: Keyord arguments passet to matplotlib axes.hist.
        '''
        data = np.loadtxt(fname)
        self.fig.clear()
        if quantity == 'v':
            xlabel = 'absolute displacement'
            h_data = np.array([(l[2]**2+l[3]**2)**0.5 for l in data])
        elif quantity == 'v_x':
            xlabel = 'x displacement'
            h_data = np.array([l[2] for l in data])
        elif quantity == 'v_y':
            xlabel = 'y displacement'
            h_data = np.array([l[3] for l in data])
        ax = self.fig.add_subplot(111)
        if log_scale:
            ax.set_yscale("log")
        ax.hist(h_data, bins, label=quantity, **kw)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('number of vectors')
        self.fig.canvas.draw()

    def show_profiles(self, fname, orientation, **kw):
        '''Plot velocity profiles.

        Line plots of the velocity component specified.

        Args:
            fname (str): A filename containing vector data.
            orientation (str): 
                horizontal: Plot v_y over x.
                vertical: Plot v_x over y.
            **kw: Keyord arguments passet to matplotlib axes.plot.
        '''
        data = np.loadtxt(fname)
        dim_x, dim_y = get_dim(data)
        self.fig.clear()
        p_data = []
        if orientation == 'horizontal':
            xlabel = 'x position'
            ylabel = 'y displacement'
            for i in range(dim_y):
                p_data.append(data[dim_y*i:dim_y*(i+1),3])            
        elif orientation == 'vertical':
            xlabel = 'y position'
            ylabel = 'x displacement'
            for i in range(dim_x):
                p_data.append(data[i::dim_x,2])
        ax = self.fig.add_subplot(111)            
        for p in p_data:
            ax.plot(range(dim_y), p, '.-', **kw)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        self.fig.canvas.draw()

    def show_scatter(self, fname, **kw):
        '''Scatter plot.

        Plots v_y over v_x.

        Args:
            fname (str): Name of a file containing vector data.
        '''
        data = np.loadtxt(fname)
        v_x = data[:,2]
        v_y = data[:,3]
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.scatter(v_x, v_y, label='scatter')
        ax.set_xlabel('x displacement')
        ax.set_ylabel('y displacement')
        self.fig.canvas.draw()
    
    def show_vec(self, fname, **kw):
        '''Display a vector plot.

        Args:
            fname (str): Pathname of a text file containing vector data.
            **kw: Keyword arguments passed to matplotlib axes.quiver.
        '''
        data = np.loadtxt(fname)
        invalid = data[:, 4].astype('bool')
        # tilde means invert:
        valid = ~invalid
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.quiver(data[invalid, 0],
                  data[invalid, 1],
                  data[invalid, 2],
                  data[invalid, 3],
                  color='r',
                  label='invalid', **kw)
        ax.quiver(data[valid, 0],
                  data[valid, 1],
                  data[valid, 2],
                  data[valid, 3],
                  color='b',
                  label='valid', **kw)
        if self.p['invert_yaxis']:
            for ax in self.fig.get_axes():
                ax.invert_yaxis()
        ax.set_xlabel('x position')
        ax.set_ylabel('y position')
        self.fig.canvas.draw()

    def show_img(self, fname):
        '''Display an image.

        Args:
            fname (str): Pathname of an image file.
        '''
        img = piv_tls.imread(fname)
        print('image data type: {}'.format(img.dtype))
        print('max count: {}'.format(img.max()))
        print('min count {}:'.format(img.min()))
        if 'int' not in str(img.dtype):
            print('Warning: For PIV processing, ' +
                  'image will be converted to np.dtype int32. ' +
                  'This may cause a loss of precision.')
        self.fig.clear()
        self.fig.add_subplot(111).matshow(img, cmap=plt.cm.Greys_r)
        self.fig.canvas.draw()

    def destroy(self):
        '''Destroy the OpenPIV GUI.

        Settings are automatically saved.
        '''
        self.get_settings()
        self.p.dump_settings(self.p.params_fname)
        tk.Tk.destroy(self)


if __name__ == '__main__':
    openPivGui = OpenPivGui()
    openPivGui.mainloop()