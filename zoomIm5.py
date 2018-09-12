import Tkinter as tk
import matplotlib as mpl

mpl.use('TkAgg')
import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from matplotlib.widgets import RectangleSelector
import sys
import time

from new_slide_hist4 import HistUpdater

fr = {'bg':'black'} 

class ImageViewer(tk.Frame):
    
    def __init__(self, master, img_data,  *args, **kwargs):
        tk.Frame.__init__(self, master,  background='black') #*args, **kwargs)
        
        self.master = master
       
########################################
#       ATTRIBUTES
########################################

#       Whole image view binning factor
        self.main_img_scale =  4
        self.binning_factor = self.main_img_scale        
#       scale slider factors
        self.min_ydim = self.min_xdim = 20
        self.init_ydim = self.init_xdim = 500
        self.n_scale_factors = 15
        self.min_scale_factor = self.min_xdim / float(self.init_ydim )
        self.scale_from_ = self.min_scale_factor
        self.scale_to  =  1. #1. / self.min_scale_factor
        self.scale_increment = (self.scale_to - self.scale_from_) / self.n_scale_factors
        self.time_of_prev_call = np.inf
        self.attached = False
        self.showing_zoom_window = True
        self.showing_range_slider = True
        self.scale = 1
        self.dragging_selector = True
        self.dragging_lower_right = True  
#       load the image
        self.img = img_data
        self.rectprops = dict(facecolor='none', edgecolor = '#00fa32',fill=False)
        self.show_pixel_values=False
        self.ymin = None
        self.holding_zoom_master = False
        self.holding_rs = False
        self.holding_the_rect = False
        self.vmin = self.vmax = None
        self.time_since_last_call = time.time()
        self.min_redraw_time = .3
        self.press_data = None

#####################################
#       WIDGETS
#####################################
        self._define_on_master_close()
        
#       MASTER FRAME IMAGE INITIALIZATION
        self._make_master_image_frame()
        
        self._create_master_frame_figure()    
        self._setup_master_image_canvas()
        
        self._add_master_frame_image()
        self._draw_master_image()
       
#       ZOOM IMAGE
        self._setup_zoom_figure()
        self._pack_zoom_figure_into_canvas()
        self._load_zoom_image_into_figure()
        #self._initialize_crosshair()
        self._draw_zoom_image()

#       IMAGE INTERACTION
        self._setup_range_slider_frame()
        self._add_range_slider()
        self._add_zoom_scale_widget()
        self._add_show_zoom_window_widget()
#       ########

        self._setup_selector()

#       #######
        self.RS.set_active(True) 
        self.RS.extents = (0,100,0,100) 
        self._sync_zoomwindow_to_selector() 

        self._set_key_bindings()
        self._menu_bar()
#####################
#       WIDGET WATCHER
        self._widget_watcher()

    def _show_zoom_window(self):
        if self.showing_zoom_window:
            return
        self.zoom_master.deiconify()
        self.RS.set_active(False)
        self.zoom_master.update()

    def _show_range_slider(self):
        if self.showing_range_slider:
            return
        self.slider_master.deiconify()
        self.slider_master.update()

    def _menu_bar(self):
        self.menu = tk.Menu(self.master)
        filemenu = tk.Menu(self.menu, tearoff=0)
        filemenu.add_command(label="Show zoom window", command=self._show_zoom_window)
        filemenu.add_command(label="Show colorscale slider", command=self._show_range_slider)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        self.menu.add_cascade(label="Image", menu=filemenu)
        self.master.config(menu=self.menu)

    def _set_key_bindings(self):
        #self.master.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.master.bind_all("<Command-z>", self._zoom_in)
        self.master.bind_all("<Command-Shift-z>", self._zoom_out)
        
        self.master.bind_all("<Shift-Left>", self._move_left)
        self.master.bind_all("<Shift-Right>", self._move_right)
        self.master.bind_all("<Shift-Up>", self._move_up)
        self.master.bind_all("<Shift-Down>", self._move_down)
        
        self.master.bind_all( "<Command-Right>", self._expand_X)
        self.master.bind_all( "<Command-Left>", self._compress_X)
        self.master.bind_all( "<Command-Down>", self._expand_Y)
        self.master.bind_all( "<Command-Up>", self._compress_Y)

        self.master.bind_all("<Left>", self._move_left_slow)
        self.master.bind_all("<Right>", self._move_right_slow)
        self.master.bind_all("<Up>", self._move_up_slow)
        self.master.bind_all("<Down>", self._move_down_slow)

    def _expand_X(self, event, inc=5):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2+inc,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _compress_X(self, event, inc=5):
        x1,x2,y1,y2 = self.RS.extents
        if x2-inc < x1:
            return
        self.RS.extents = (x1, x2-inc,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _expand_Y(self, event, inc=5):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2,y1,y2+inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
        
    def _compress_Y(self, event, inc=5):
        x1,x2,y1,y2 = self.RS.extents
        if y2-inc < y1:
            return
        self.RS.extents = (x1, x2,y1,y2-inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()

    def _zoom_in(self, event):
        curr_val = self.scale
        if not self.showing_range_slider:
            next_val = max( curr_val - self.scale_increment/2., self.min_scale_factor)
            self._set_zoom_scale( next_val)
        else:
            self.zoom_scale_slider.set( curr_val - self.scale_increment/2.)
    
    def _zoom_out(self, event):
        curr_val = self.scale
        if not self.showing_range_slider:
            next_val = min( curr_val + self.scale_increment/2., 1)
            self._set_zoom_scale( next_val)
        else:
            self.zoom_scale_slider.set(curr_val + self.scale_increment/2.)

    def _move_left(self, event, inc=10):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1-inc, x2-inc,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _move_left_slow(self, event):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1-1, x2-1,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()

    def _move_down(self, event, inc=10):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2,y1+inc,y2+inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _move_down_slow(self, event, inc=1):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2,y1+inc,y2+inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()

    def _move_right(self, event, inc=10):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1+inc, x2+inc,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _move_right_slow(self, event, inc=1):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1+inc, x2+inc,y1,y2)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _move_up(self, event, inc=10):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2, y1-inc,y2-inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _move_up_slow(self, event, inc=1):
        x1,x2,y1,y2 = self.RS.extents
        self.RS.extents = (x1, x2, y1-inc,y2-inc)
        self._sync_zoomwindow_to_selector()
        self.zoom_fig.canvas.draw()
    
    def _define_on_master_close(self):
        self.master.protocol("WM_DELETE_WINDOW", self._on_master_window_close)
        self.master.config(bg="black")
    
    def _make_master_image_frame(self):
        self.image_frame = tk.Frame( self.master, **fr )
        self.image_frame.pack( side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

    def _on_master_window_close(self):
        self.master.destroy()
        print("\n\tBoo!!!\n")
        sys.exit()

    def _setup_range_slider_frame(self):
        self.slider_master = tk.Toplevel()
        self.slider_master.pack_propagate(True)
        
        self.slider_frame = tk.Frame( self.slider_master , **fr)
        self.slider_frame.pack( side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        
        self.slider_master.protocol("WM_DELETE_WINDOW", self._on_range_slider_close)

    def _widget_watcher(self):
        
        new_vmin, new_vmax = self.hist_updater.minval, self.hist_updater.maxval
        if new_vmin != self.vmin or new_vmax != self.vmax:
            t = time.time()
            print("chaning clim")
            self.vmin = new_vmin
            self.vmax = new_vmax
            self._im.set_clim( vmin=self.vmin, vmax=self.vmax)
            self._zoom_im.set_clim( vmin=self.vmin, vmax=self.vmax)
            self._update_zoom_image()
            self._update_master_image()
            print time.time()-t
        
        if self.holding_rs:
            t = time.time()
            print("Holding that REECT")
            #self._sync_zoomwindow_to_selector()
            self._update_zoom_image()
            print time.time()-t
        
        if self.holding_zoom_master:
            print("Holding zoomwind")
            t = time.time()
            self._update_zoom_image()
            print time.time()-t
        
        self.master.after( 50, self._widget_watcher)


    def _add_range_slider(self):
        self.hist_updater = HistUpdater( self.slider_frame, 
            self.img.ravel(), label='pixels', color='#00fa32', plot=False, range_slider_len=800, 
            background='black', ims =None) # [ (self._im, self.canvas), (self._zoom_im, self.zoom_canvas)   ])
        self.hist_updater.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        self.hist_updater.pack_propagate()
    
    def _create_master_frame_figure(self):
        self.fig = plt.figure(figsize=(6,6))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        #self.ax.set_facecolor("black") 
        self.fig.patch.set_visible(False)
        self.ax.axis('off')
        

    def _add_master_frame_image(self):
        self._im = self.ax.imshow(
            self.img[::self.binning_factor, ::self.binning_factor], 
            interpolation='nearest', 
            vmin=self.vmin, 
            vmax=self.vmax,
            #aspect='equal',
            cmap='gist_gray')
        
        self.vmin, self.vmax = self._im.get_clim()

    def _set_zoom_scale(self, value):
        value = float(value)
        self.scale =  value
        
        self._sync_selector_to_zoomwindow_on_rescale()
        self._update_zoom_image()
        
    def _launch_zoom_window(self):
        if self.showing_zoom_window:
            return
        
        self._setup_zoom_figure()
        self._pack_zoom_figure_into_canvas()
        self._load_zoom_image_into_figure()
        self._draw_zoom_image()
   
        

    def _add_zoom_scale_widget(self):
        
        self.zoom_scale_slider = tk.Scale( self.slider_frame, from_=self.scale_from_, to=self.scale_to,
                                resolution=self.scale_increment/2., fg="#00fa32", bg='black', 
                                length=200,highlightbackground="#00fa32", 
                                highlightthickness=0, orient=tk.HORIZONTAL, 
                                command=self._set_zoom_scale)
        self.zoom_scale_slider.pack( side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.zoom_scale_slider.set( 0.5)
    

    
    def _add_show_zoom_window_widget(self):
        self._show_window_button = tk.Button(self.slider_frame, 
            text="Show zoom window", 
            command=self._launch_zoom_window) 
        self._show_window_button.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
      

    def _setup_master_image_canvas(self):
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.image_frame) 
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.canvas.get_tk_widget().configure(bg='black', highlightbackground="black")
            
    def _setup_zoom_figure(self):
        self.zoom_fig = plt.figure( figsize=(3,3))
        self.zoom_ax = self.zoom_fig.add_axes([0.01,0.01,.98,.98])
        
        #self.zoom_fig.patch.set_visible(False)
        self.zoom_ax.axis('off')
        
        self.zoom_ax.spines['bottom'].set_color('#00fa32')
        self.zoom_ax.spines['right'].set_color('#00fa32')
        self.zoom_ax.spines['left'].set_color('#00fa32')
        self.zoom_ax.spines['top'].set_color('#00fa32')
        
        #self.zoom_ax.set_xticks([])
        #self.zoom_ax.set_yticks([])
        

    def _load_zoom_image_into_figure(self):
        self._zoom_im = self.zoom_ax.imshow( self.img, 
                vmin=self.vmin, 
                vmax=self.vmax, 
                interpolation='nearest',
                aspect='auto', 
                cmap='gist_gray')
        
        self.img_extent = (0,self.img.shape[1], 0, self.img.shape[0] ) 
    
    def _initialize_crosshair(self):
        
        x1 = y1 = 0
        y2,x2 = self.img.shape

        self.zoom_ax.set_xlim(x1,x2)
        self.zoom_ax.set_ylim(y2,y1)
        
        Xmid = .5*(x1 + x2)
        Ymid = .5*(y1 + y2)

        #self.zoom_crosshair_Hline = self.zoom_ax.plot( 
        #    [ Ymid, Ymid  ], [x1, x2], 
        #    ls='--', color='#00fa32')
        
        #self.zoom_crosshair_Vline = self.zoom_ax.plot( 
        #    [ y1, y2  ], [Xmid, Xmid], 
        #    ls='--',color='#00fa32')
    
    def _on_zoom_master_close(self):
        self.showing_zoom_window=False
        self.RS.set_active(False)
        #for patch in self.RS_artists:
        #    artist.set_visible(False)
        #self.ax.patches[0].set_visible(False)
        self.zoom_master.withdraw()
    
    def _on_range_slider_close(self):
        self.showing_range_slider=False
        self.slider_master.withdraw()

    def _on_click_zoom_master(self, event):
        self.holding_zoom_master = True

    def _on_release_zoom_master(self, event):
        self.holding_zoom_master = False
   
    def _pack_zoom_figure_into_canvas(self):
        self.zoom_master = tk.Toplevel(self.master)
        self.zoom_master.protocol("WM_DELETE_WINDOW", self._on_zoom_master_close)
        
        self.zoom_master.bind( "<Button-1>", self._on_click_zoom_master)
        self.zoom_master.bind( "<ButtonRelease-1>", self._on_release_zoom_master)
        self.zoom_master.bind( "<Configure>", self._on_mousemove_zoom_master)
        
        self.zoom_master.pack_propagate(True)
        
        self.zoom_canvas = FigureCanvasTkAgg(self.zoom_fig, master=self.zoom_master)
        self.zoom_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=tk.YES)
        self.zoom_canvas.get_tk_widget().configure(bg='black', highlightbackground="black", bd=1 ) 
        #self.showing_zoom_window = True
  


#############################
#   DRAW AND UPDATE IMAGES!
#############################
    def _draw_master_image(self):
        self.canvas.draw_idle()
        self.canvas.flush_events()
    
    def _update_master_image(self):
        self.ax.draw_artist(self._im)
        
        for artist in self.RS_artists:
            self.ax.draw_artist( artist)
        
        self.fig.canvas.blit(self.ax.bbox)
        self.canvas.flush_events()
    
    def _draw_zoom_image(self):
        self.zoom_fig.canvas.draw_idle()
        self.zoom_fig.canvas.flush_events()
    
    def _update_zoom_image(self):
        self.zoom_ax.draw_artist( self._zoom_im)
        #self.zoom_ax.draw_artist( self.zoom_crosshair_Hline[0] )
        #self.zoom_ax.draw_artist( self.zoom_crosshair_Vline[0] )
        self.zoom_fig.canvas.blit( self.zoom_ax.bbox)
        self.zoom_fig.canvas.flush_events()
    

    def _update_zoom_image_data(self):
        self.zoom_ax.draw_artist( self._zoom_im)
        self.zoom_fig.canvas.blit( self.zoom_ax.bbox)
        self.zoom_fig.canvas.flush_events()

#####################################
#   DYNAMIC ZOOM IMAGE CALLBACKS
#####################################
    def _on_mousemove_zoom_master(self, event):
        if self.holding_zoom_master:
            self._sync_selector_to_zoomwindow()
    
    def _sync_selector_to_zoomwindow_on_rescale(self):
        
        cent_x, cent_y = self.RS.center
        
        zoom_window_height = self.zoom_master.winfo_height()
        zoom_window_width = self.zoom_master.winfo_width()
       
        if self.dragging_lower_right:
            new_x1 = cent_x - .5*zoom_window_width/ float(self.binning_factor) * self.scale
            new_y1 = cent_y - .5*zoom_window_height/ float(self.binning_factor) * self.scale
            
            new_x2 = cent_x + .5*zoom_window_width/ float(self.binning_factor) * self.scale
            new_y2 = cent_y + .5*zoom_window_height/ float(self.binning_factor) * self.scale
            
            self.RS.extents = (new_x1,new_x2,new_y1,new_y2)


        w = zoom_window_width*self.scale
        h = zoom_window_height*self.scale
       
        img_cent_x = (self.img_extent[0] + self.img_extent[1])*.5
        img_cent_y = (self.img_extent[2] + self.img_extent[3])*.5

        x1 = img_cent_x - w/2.
        y1 = img_cent_y - h/2.
        
        x2 = img_cent_x + w/2.
        y2 = img_cent_y + h/2.
        
        self.img_extent = (x1,x2,y1,y2)
        self._zoom_im.set_data( self.img[ int(y1):int(y2), 
                        int(x1):int(x2)] )

#       axis limitation
        #self.zoom_ax.set_xlim(x1,x2)
        #self.zoom_ax.set_ylim(y2,y1)
        
#       cross hair
        #Ymid = (y1 +y2)*.5
        #Xmid = (x1+x2)*.5
        
        #self.zoom_crosshair_Hline[0].set_xdata( [Ymid, Ymid] ) 
        #self.zoom_crosshair_Hline[0].set_ydata( [x1, x2])
        
        #self.zoom_crosshair_Vline[0].set_xdata( [y1,y2])
        #self.zoom_crosshair_Vline[0].set_ydata( [Xmid, Xmid])
    
    
    def _sync_selector_to_zoomwindow(self):
       
        old_x1, old_x2, old_y1, old_y2 = self.RS.extents
        
        zoom_window_height = self.zoom_master.winfo_height()
        zoom_window_width = self.zoom_master.winfo_width()
       
        if self.dragging_lower_right:
            new_x1 = old_x1
            new_y1 = old_y1
            new_x2 = old_x1 + zoom_window_width/ float(self.binning_factor) * self.scale
            new_y2 = old_y1 + zoom_window_height/ float(self.binning_factor) * self.scale
            
            self.RS.extents = (new_x1,new_x2,new_y1,new_y2)

        x1 = self.img_extent[0]
        y1 = self.img_extent[2]
        x2 = zoom_window_width*self.scale  + x1
        y2 = zoom_window_height*self.scale  + y1
        self.img_extent = (x1,x2,y1,y2)
        self._zoom_im.set_data( self.img[ int(y1):int(y2), 
                        int(x1):int(x2)] )
        
#       axis limitation
        #self.zoom_ax.set_xlim(x1,x2)
        #self.zoom_ax.set_ylim(y2,y1)
        
#       cross hair
        #Ymid = (y1 +y2)*.5
        #Xmid = (x1+x2)*.5
        #self.zoom_crosshair_Hline[0].set_xdata( [Ymid, Ymid] ) 
        #self.zoom_crosshair_Hline[0].set_ydata( [x1, x2])
        
        #self.zoom_crosshair_Vline[0].set_xdata( [y1,y2])
        #self.zoom_crosshair_Vline[0].set_ydata( [Xmid, Xmid])

    def _sync_zoomwindow_to_selector(self):
#       geometry
        x1,x2,y1,y2 = [ i * self.binning_factor  for i in self.RS.extents ]
        
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        width = (x2-x1) 
        height = (y2-y1)
        Ymid = .5*(y1 + y2)
        Xmid = .5*(x1 + x2)
       
        #print( width, height)
        #print  [ int(Ymid - height/2.), int(Ymid +height/2.), int(Xmid-width/2.), int(Xmid + width/2.)]

#       zoom image
        self.img_extent = ( int(Xmid-width/2.), int(Xmid + width/2.), int(Ymid - height/2.), int(Ymid +height/2.) )
        self._zoom_im.set_data(  self.img[ int(Ymid - height/2.):int(Ymid +height/2.), 
                                        int(Xmid-width/2.):int(Xmid + width/2.)] )
        
#       axis limitation
        #self.zoom_ax.set_xlim(x1,x2)
        #self.zoom_ax.set_ylim(y2,y1)
        
#       cross hair
        #self.zoom_crosshair_Hline[0].set_xdata( [Ymid, Ymid] ) 
        #self.zoom_crosshair_Hline[0].set_ydata( [x1, x2])
        
        #self.zoom_crosshair_Vline[0].set_xdata( [y1,y2])
        #self.zoom_crosshair_Vline[0].set_ydata( [Xmid, Xmid])
        
#       sync window size
        #self.zoom_canvas.xview_scroll(int( width), "units")
        #self.zoom_canvas.yview_scroll(int(height), "units")
        self.zoom_master.geometry("%dx%d" %(int(width/self.scale), int(height/self.scale)))
        
    def _setup_selector(self):
        artists =  self.ax.get_children()
        self.RS = RectangleSelector(self.ax, self._on_rectangle_selection,
                                       drawtype='box', useblit=False,
                                       button=[1, 3], 
                                       minspanx=2, minspany=2,
                                       spancoords='data',
                                       interactive=True,
                                       rectprops=self.rectprops)

        self.RS_artists = [ a for a in self.ax.get_children() if a not in artists]
        
        self.RS_rectangle = [a for a in self.RS.artists if type(a) == mpl.patches.Rectangle ]
        assert( len(self.RS_rectangle)==1)
        self.RS_rectangle = self.RS_rectangle[0]
        
        self.RS_rectangle.figure.canvas.mpl_connect('motion_notify_event', self.on_rs_motion)
        self.RS_rectangle.figure.canvas.mpl_connect('button_press_event', self.on_rs_press)
        self.RS_rectangle.figure.canvas.mpl_connect('button_release_event', self.on_rs_release)
    
    def _on_rectangle_selection(self, press, release):
        """
        widget passes press and release to this callback
        """
        self._sync_zoomwindow_to_selector()
        #self._update_zoom_image()    
    
    def on_rs_press(self, event):
        self.holding_rs = True
        #self.zoom_master.lift()
        print ("clicked rs")
    
    def on_rs_release(self, event):
        self.holding_rs = False
        print ("released rs")

    def on_rs_motion(self, event):
        if self.holding_rs:
            self._sync_zoomwindow_to_selector()
            self._zoom_im.figure.canvas.draw()
    
    

if __name__ == '__main__':
    #img = np.random.random(  (1500,1500) )
    #Y,X = np.indices( img.shape)
    #img = np.sin(X**2/ 10000.)**2 *np.cos(Y**2/10000.)*3

    import h5py
    f = h5py.File("/Users/damende/a2a_randpeaks/a2a_beta.20+.cxi")
    #f = h5py.File("testdd")
    img = f['data'][0]
    #img [ img > 1000] = 0
    
    root = tk.Tk()
    im = ImageViewer(root, img, background='black')
    im.pack(fill=tk.BOTH, expand=tk.YES)
    
    root.mainloop()

