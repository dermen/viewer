try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import  matplotlib as mpl
from matplotlib.figure import Figure
mpl.use('TkAgg')
import pylab as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


labstyle={'bg':'snow', 'fg':'black'}
fr = {'bg':'black'}
frpk = {'padx':5, 'pady':5}
class HistUpdater(tk.Frame):
    '''Illustrate how to drag items on a Tkinter canvas'''
    def __init__(self, parent, data, color='blue', label='label', 
            max_bins=1000):
       
        tk.Frame.__init__(self, parent,)
        
        self.fig = plt.figure()
        self.ax = plt.gca()

        self.color = color
        
        self.label = label
        self._set_fig_title()


        
        self.dat = data
        self.minval = self.dat.min()
        self.maxval = self.dat.max()

        self.Ndat = len(self.dat)
        self.dmax = max( self.dat)
        self.dmin = min(self.dat)

        self.max_nbin = min(int(self.Ndat*.5), max_bins)
        #self.max_nbin = 1000 #min(int(self.Ndat*.5), max_bins)
        #self.max_nbin = self.Ndat
        self.smallest_bins = np.linspace(self.dmin, self.dmax, self.max_nbin)

        self.smallest_width = self.smallest_bins[1] - self.smallest_bins[0]
        self.smallest_bins = np.append( self.smallest_bins-.5*self.smallest_width, \
                                self.smallest_bins[-1]+self.smallest_width)
#       frames
        self.container_frame = tk.Frame( self, **fr)
        self.container_frame.pack(side=tk.TOP, expand=True, **frpk)


        mainframe = tk.Frame(self.container_frame, **fr)
        mainframe.pack(side=tk.TOP, expand=True, **frpk)
        
        self.mainframe2 = tk.Frame(self.container_frame, **fr)
        self.mainframe2.pack(side=tk.TOP, expand=True, **frpk)


        self.range_slider_len = 400
        self.range_slider_height= 60
        self.range_slider_token_height=40
        self.range_slider_token_halfheight=20
        self.token_text_vertical_position=10
        self.range_slider_token_vertical_offset = 20
        self.range_slider_token_width = 10
        self.range_slider_token_halfwidth = 5
        self.range_slider_token_LHS_offset = 30
        self.range_slider_token_RHS_offset = 30
        self.text_offset = 15
        self.range_slider_value_range = self.range_slider_len \
            -2*self.range_slider_token_width - self.range_slider_token_LHS_offset\
            -self.range_slider_token_RHS_offset
        
        self.range_slider_maxRHS = self.range_slider_len - self.range_slider_token_halfwidth - self.range_slider_token_RHS_offset

        self.range_slider_minLHS = self.range_slider_token_halfwidth + self.range_slider_token_LHS_offset
        

#       create a canvas for drawing the range-slider...
        tk.Label(mainframe, text=label, \
            **labstyle).pack(side=tk.LEFT, fill=tk.BOTH, **frpk)
        self.canvas = tk.Canvas(mainframe, width=self.range_slider_len, 
            height=self.range_slider_height, bg='white')
        self.canvas.pack(expand=True, side=tk.LEFT, **frpk)
       
#       reate orizontal line sepcifying the slider token track
        self.canvas.create_line( ( self.range_slider_token_LHS_offset, 
            self.range_slider_token_vertical_offset+self.range_slider_token_halfheight, 
            self.range_slider_len-self.range_slider_token_RHS_offset, 
            self.range_slider_token_vertical_offset+self.range_slider_token_halfheight))
        
#       create a vertical line along the data mean
        dat_mean = np.mean(data)
        vert_line_pos= (dat_mean-self.dmin)* self.range_slider_value_range \
            / (self.dmax - self.dmin)
        
        self.canvas.create_line( ( vert_line_pos, 
            self.range_slider_token_vertical_offset, 
            vert_line_pos, 
            self.range_slider_token_vertical_offset+self.range_slider_token_height))

#       set a single bar slider for adjusting the binning
        self.binning_slider = tk.Scale(mainframe, from_=0.01, to=.9999, resolution=0.01, 
            orient=tk.VERTICAL, command=self._scale_update_hist,
            length=50, sliderlength=10, width=40)
        self.binning_slider.pack( expand=True, side=tk.LEFT,  **frpk)
        self.binning_slider.set(0.2)

#       this data is used to keep track the slider components as they are dragged
        self._drag_data = {"x": 0, "y": 0, "item": None}

#       create a couple of movable sliders
        i1 = self._create_token((self.range_slider_minLHS, 
            self.range_slider_token_vertical_offset+self.range_slider_token_halfheight), 
            self.color)
        i2 = self._create_token((self.range_slider_maxRHS,
            self.range_slider_token_vertical_offset+self.range_slider_token_halfheight), 
            self.color)
        self.items = [i1, i2] # store the IDs
        
#       TEXT LABEL
        self.minvaltext = self.canvas.create_text( 
            self.range_slider_minLHS-self.text_offset, 
            self.token_text_vertical_position, text="%.2f"%self.dmin, fill='black')
        self.maxvaltext = self.canvas.create_text( 
            self.range_slider_maxRHS+self.text_offset, 
            self.token_text_vertical_position, text="%.2f"%self.dmax, fill='black')
        
        #   set the figure canvas for the histogram plots
        self._setup_fig_canvas()

#       make first histogram plots
        self._set_bins(bin_frac=0.1)
        self._make_bar_plots()
        self._set_bar_heights()
        self._draw_hist()
        
        # add bindings for clicking, dragging and releasing over
        # any object with the "token" tag
        self.canvas.tag_bind("token", "<ButtonPress-1>", self.on_token_press)
        self.canvas.tag_bind("token", "<ButtonRelease-1>", self.on_token_release)
        self.canvas.tag_bind("token", "<B1-Motion>", self.on_token_motion)
        
    def _set_fig_title(self):
        (x0,y0), (x1,y1) = self.ax.get_position().get_points() # axis border boundary
        ypos = y1 # - (y1-y0)*.1
        self.fig.text((x0+x1)*.5, ypos, self.label, backgroundcolor='w', color='k', 
            alpha=.5, horizontalalignment='left')


    def _scale_update_hist(self, bin_frac):
        self._set_bins(float(bin_frac))
        self._set_bar_heights()
        self._update_bar_binnings()
        self._draw_hist()
    
    def _range_slider_update_hist(self):
        self._set_bar_heights()
        self._update_bars()
        self.fig_canvas.draw()

    def _set_bins(self, bin_frac):
        self.nbins = int( bin_frac * self.max_nbin)
        self.bin_pos = [ i[0] for i in np.array_split( np.arange( self.max_nbin), self.nbins) ]
        self.bins = [ self.smallest_bins[i] for i in self.bin_pos]
        self.width = self.bins[1] - self.bins[0]
        self.Hbins = np.append(self.bins - self.width*.5, self.bins[-1] + self.width)

    def _set_bar_heights(self):
        truncated_dat = self.dat[  np.logical_and( self.dat >= self.minval, self.dat <= self.maxval)  ]
        self.bar_heights, _ = np.histogram( truncated_dat, bins=self.Hbins)
        self.ax.set_ylim(0, self.bar_heights.max()) #*1.1)

    def _make_bar_plots(self):
        #self.ax.cla()
        init_heights = np.zeros(self.smallest_bins.shape[0]) 
        self.bar_plots = self.ax.bar(self.smallest_bins, 
            init_heights, color=self.color, align='edge')

    def _setup_fig_canvas(self):
        #toplvl = tk.Toplevel(self.master)
        self.disp_frame = tk.Frame( self.mainframe2 )
        self.disp_frame.pack( side=tk.TOP, expand=1, fill=tk.BOTH )
        
        self.fig_canvas = FigureCanvasTkAgg(self.fig, master=self.disp_frame)
        self.fig_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(self.fig_canvas, self.disp_frame)
        toolbar.update()
        self.fig_canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def _draw_hist(self):
        #self.fig.canvas.draw()
        #KJADKSDJKASJDKASJKDJASKJDKASJD
        self.fig_canvas.draw()

    def _update_bars(self):
        #inserts = np.searchsorted( self.global_bins, self.bins-self.width*.5 )
        for i,i_smallest in enumerate( self.bin_pos):
            B = self.bar_plots[i_smallest]
            B.set_height(self.bar_heights[i])

    def _update_bar_binnings(self):
        for i,B in enumerate(self.bar_plots):
            B.set_height(0)
        #inserts = np.searchsorted( self.global_bins, self.bins-self.width*.5 )
        for i,i_smallest in enumerate( self.bin_pos):
            B = self.bar_plots[i_smallest]
            B.set_width(self.width) 
            B.set_height( self.bar_heights[i] )
    
    def _create_token(self, coord, color):
        '''Create a token at the given coordinate in the given color'''
        (x,y) = coord
        return self.canvas.create_rectangle(x-self.range_slider_token_halfwidth, 
            y-self.range_slider_token_halfheight, 
            x+self.range_slider_token_halfwidth, 
            y+self.range_slider_token_halfheight, 
            outline=color, fill=color, tags="token")

    def on_token_press(self, event):
        '''Begining drag of an object'''
        # record the item and its location
        self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        self._drag_data["x"] = event.x

    def on_token_release(self, event):
        '''End drag of an object'''
        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0

    def on_token_motion(self, event):
        '''Handle dragging of an object'''
        clicked_item = self._drag_data["item"]
        coors = self.canvas.coords(clicked_item)
        xleft, ybottom, xright, ytop = coors
        clicked_x = .5* (xleft + xright)
        clicked_y = .5* (ybottom + ytop)
        
        other_item = [i for i in self.items if i != clicked_item][0]
        other_coors = self.canvas.coords(other_item)
        other_x = .5*(other_coors[0] + other_coors[2])
        other_y = .5*(other_coors[1]+ other_coors[3])
        if clicked_x > other_x:
            #   RIGHT HAND SIDE ITEM
            delta_x = event.x - self._drag_data["x"]
            
            x_new = min( clicked_x + delta_x, self.range_slider_maxRHS) 
            x_new = max( x_new, other_x+self.range_slider_token_width) 

            self.canvas.coords( clicked_item, (x_new-self.range_slider_token_halfwidth, 
                clicked_y-self.range_slider_token_halfheight, 
                    x_new+self.range_slider_token_halfwidth, 
                    clicked_y+self.range_slider_token_halfheight))
            self.canvas.coords( self.maxvaltext, (x_new+self.text_offset,
                self.token_text_vertical_position))
            self.canvas.itemconfig( self.maxvaltext, text="%.2f"%self.maxval)
            
            new_drag = min( self.range_slider_maxRHS,  event.x)
            new_drag = max(  other_x , new_drag)
            self._drag_data["x"] = new_drag 
            
            self.maxval = ( (x_new) / self.range_slider_value_range ) \
                * ( self.dmax - self.dmin ) + self.dmin
            
        else:
            #   LEFT HAND SIDE ITEM
            delta_x = event.x - self._drag_data["x"]
            
            x_new = max( clicked_x + delta_x, self.range_slider_minLHS) 
            x_new = min( x_new, other_x-self.range_slider_token_width) 
            
            self.canvas.coords( clicked_item, 
                (x_new-self.range_slider_token_halfwidth, 
                    clicked_y-self.range_slider_token_halfheight, 
                    x_new+self.range_slider_token_halfwidth, 
                    clicked_y+self.range_slider_token_halfheight))
            self.canvas.coords( self.minvaltext, (x_new-self.text_offset, 
                self.token_text_vertical_position))
            self.canvas.itemconfig( self.minvaltext, text="%.2f"%self.minval)
            new_drag = max( self.range_slider_minLHS,  event.x)
            new_drag = min(  other_x , new_drag)
            self._drag_data["x"] = new_drag 
            
            self.minval = ((x_new) / self.range_slider_value_range ) \
                * ( self.dmax - self.dmin ) + self.dmin
            
        self._range_slider_update_hist()

    
def main():
    test_data = np.random.normal( 10,1,10000)
    test_data2 = np.random.normal( 0,2,10000)
    #test_data3 = np.random.normal( 10,1,10000)
    #test_data4 = np.random.normal( 50,5,10000)
    #test_data5 = np.random.normal( 10,1,10000)
    #test_data6 = np.random.normal( 50,5,10000)
    #DAT = [ test_data, test_data2, test_data3, test_data4, test_data5, test_data6]
    
    DAT = [ test_data, test_data2]
    
    colors = ['pink', 'lightblue']
    
    #colors = ['red', 'red', 'red', 'blue', 'blue', 'blue']
    
    labels = [ r"a (meters)", r"b ($\AA$)" ]
    root = tk.Tk()
    nrows = 2
    ncols = 1
    #fig, axs = plt.subplots( nrows=nrows, ncols=ncols )
    assert( nrows * ncols == len( DAT)) 
    #axs = axs.reshape( (nrows, ncols))
    i_ax = 0
    for i_row in xrange( nrows):
        for i_col in xrange( ncols):
            #ax = axs[i_row, i_col]
            label = labels[i_ax]
            dat = DAT[i_ax]
            color = colors[i_ax]
            HistUpdater(root, dat, color=color, label=label).pack(side=tk.LEFT, expand=0) #, fill=tk.BOTH, expand=1)
            i_ax +=1
    #plt.draw()
    #plt.pause(0.0001)
    root.mainloop()


    
if __name__ == "__main__":
    main()
