import Tkinter as tk
import matplotlib as mpl
mpl.use('TkAgg')
import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from matplotlib.widgets import RectangleSelector
import sys

from new_slide_hist import HistUpdater

plt.style.use('dark_background')

fr = {'bg':'black'} 

class ImageViewer(tk.Frame):
    
    def __init__(self, master, img_data,  *args, **kwargs):
        tk.Frame.__init__(self, master,  background='black') #*args, **kwargs)
        self.master = master

        self.master.protocol("WM_DELETE_WINDOW", self._on_master_window_close)
        self.master.config(bg="black")
        
        self.image_frame = tk.Frame( self.master, **fr )
        self.image_frame.pack( side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        
        self.attached = False
        self.showing_zoom_window = False

        self._setup_range_slider_frame()
       
        self.zoom_scale_value_mapping = {0:1, -1: .8, -2: .6, -3:.4, -4:.2, -5:.1,
                        1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2}


        self.scale = 1
        #load the image
        self.img = img_data
        self.rectprops = dict(facecolor='red', edgecolor = 'black',
                 alpha=0.2, fill=True)
        
        self._create_figure()    
        self._add_img()
        self._setup_canvas()
        self.show_pixel_values=False
        self._setup_zoom_figure()
        self._setup_selector()
        self.ymin = None
        self.RS.set_active(False)
        self.toggle_tools()
        self._zoom_im = None

        self._add_hist_updater()

        self._update_clim()
   
    def _on_master_window_close(self):
        self.master.destroy()
        print("\n\tBoo!!!\n")
        sys.exit()

    def _setup_range_slider_frame(self):
        self.slider_master = tk.Toplevel()
        self.slider_master.pack_propagate(True)
        
        self.slider_frame = tk.Frame( self.slider_master , **fr)
        self.slider_frame.pack( side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.vmin = self.vmax = None

    def _update_clim(self):
        self.vmin, self.vmax = self.hist_updater.minval, self.hist_updater.maxval
        self._im.set_clim( vmin=self.vmin, vmax=self.vmax)
        if self._zoom_im is not None:
            self._zoom_im.set_clim( vmin=self.vmin, vmax=self.vmax)
        self.canvas.draw()
        if self.showing_zoom_window:
            self.canvas2.draw()
        self.master.after( 500, self._update_clim )    

    def _add_hist_updater(self):
        self.hist_updater = HistUpdater( self.slider_frame, 
            self.img.ravel(), label='pixels', color='#00fa32', plot=False, range_slider_len=800, 
            background='black')
        self.hist_updater.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        self.hist_updater.pack_propagate()
    
    def toggle_tools(self):
        if self.toolbar._active in ['PAN','ZOOM']:
            self.use_rect_zoom_var.set(0)
            self.RS.set_active(False)
        self.master.after( 100, self.toggle_tools )

    def _create_figure(self):
        self.fig = plt.figure(figsize=(6,6))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_facecolor("black") 
        self.fig.patch.set_visible(False)
        self.ax.axis('off')

    def _add_img(self):
        self._im = self.ax.imshow(self.img, interpolation='nearest', 
            norm=None, 
            vmin=self.vmin, 
            vmax=self.vmax, 
            cmap='gist_gray')
        self.vmin,self.vmax = self._im.get_clim()
    
    def _set_rectangle_zoom(self):
        self._use_zoom = self.use_rect_zoom_var.get()
        if self._use_zoom:
            if self.toolbar._active =='PAN':
                self.toolbar.pan('off')
            if self.toolbar._active =='ZOOM':
                self.toolbar.zoom('off')
            self.RS.set_active(True)
        else:
            self.RS.set_active(False)

    def _set_zoom_scale(self, value):
        
        value = int ( value)
        
        self.scale = self.zoom_scale_value_mapping[ value]

        if self.showing_zoom_window:
           
            x_center, y_center = self.RS.center

            width = x2-x1
            height = y2-y1
            print (width, height)
            
            new_width = width * self.scale
            new_height = height * self.scale
            
            if x_center - new_width/2. < 0:
                x1_new = 0
                x2_new = int(new_width)
            elif x_center + new_width/2. > self.img.shape[1]:
                x1_new = self.img.shape[1] - int( new_width)
                x2_new = self.img.shape[1] 
            else:
                x1_new = int( x_center-new_width/2.)
                x2_new = int( x_center + new_width/2.)
            
            if y_center - new_height/2. < 0:
                y1_new = 0
                y2_new = int(new_height)
            elif y_center + new_height/2. > self.img.shape[0]:
                y1_new = self.img.shape[0] - int( new_height)
                y2_new = self.img.shape[0] 
            else:
                y1_new = int( y_center - new_height/2.)
                y2_new = int( y_center + new_height/2.)

            #self.scaled_extents = (x1_new, x2_new, y1_new, y2_new)

            self._update_RS( x1_new, x2_new, y1_new, y2_new)
            
            self._set_zoom_img_slice( x1_new,x2_new,y1_new,y2_new, resize_zoom_window=False)

    
    def _update_RS(self, xmin,xmax,ymin,ymax):
        self.RS.extents = (xmin,xmax,ymin,ymax)
        
    def _launch_zoom_window(self):
        if self.showing_zoom_window:
            return
        else:
            self._setup_zoom_space()
            self.use_rect_zoom_var.set(1)
            self._set_rectangle_zoom()
            x1,x2,y1,y2 = 10,100,10,100
            self._update_RS(x1,y1,x2,y2)
            self._set_zoom_img_slice( x1,x2,y1,y2 )

    def _setup_canvas(self):
        
        self.use_rect_zoom_var = tk.IntVar()

        self.use_rect_zoom_checkbutton = tk.Checkbutton(self.image_frame, 
                            text='Rectangle zoom', 
                            var=self.use_rect_zoom_var, 
                            command=self._set_rectangle_zoom, 
                            fg='white', bg='black')
        self.use_rect_zoom_checkbutton.pack(side=tk.TOP)


        self.zoom_scale_slider = tk.Scale( self.image_frame, from_=-5, to=5, 
                                resolution=1, fg="#00fa32", bg='black', 
                                length=200,highlightbackground="#00fa32", 
                                highlightthickness=0, orient=tk.HORIZONTAL, 
                                command=self._set_zoom_scale)
        self.zoom_scale_slider.pack( side=tk.TOP, fill=tk.X, expand=tk.YES)

        self.zoom_scale_slider.set(0)

        self._show_window_button = tk.Button(self.image_frame, text="Show zoom window", command=self._launch_zoom_window) 
        self._show_window_button.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.image_frame) 
        self.canvas.get_tk_widget().configure(bg='black', highlightbackground="black")
        self.canvas.get_tk_widget().pack(side=tk.TOP, 
            expand=tk.YES, fill=tk.BOTH)
        
#       NOTE: https://github.com/matplotlib/matplotlib/issues/6781 - dissapears on resize, consider fix 
        self.toolbar = NavigationToolbar2Tk(self.canvas, 
            self.slider_frame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, 
            expand=tk.YES, fill=tk.BOTH)

    def _setup_zoom_figure(self):
        self.zoom_fig = plt.figure(2)
        self.zoom_ax = self.zoom_fig.add_axes([0,0,1,1])
        self.zoom_fig.patch.set_visible(False)
        self.zoom_fig.canvas.toolbar.pack_forget()
        self.zoom_ax.axis('off')

        self._load_zoom_image_into_figure()

    def _load_zoom_image_into_figure(self):
        self.zoom_ax.imshow(  self.img, 
                vmin=self.vmin, 
                vmax=self.vmax, 
                interpolation='nearest',
                aspect='auto', 
                cmap='gist_gray')


    def _on_zoom_master_close(self):
        self.showing_zoom_window=False
        self.use_rect_zoom_var.set(0)
        self._set_rectangle_zoom()
        self.ax.patches[0].set_visible(False)
        self.zoom_master.destroy()


    def _on_zoom_master_resize(self, event):
        
        width, height = event.width, event.height
        
        x1,x2,y1,y2 = self.RS.extents

        x2_new = x1 + width
        y2_new = y1 + height
        
        self._update_RS( x1,x2_new,y1,y2_new)
        self._set_zoom_img_slice(x1,x2_new, y1,y2_new, resize_zoom_window=False) 

    def _setup_zoom_space(self):
        
        self.zoom_master= tk.Toplevel(self.master)
        self.zoom_master.protocol("WM_DELETE_WINDOW", self._on_zoom_master_close)
        self.zoom_master.bind("<Configure>", self._on_zoom_master_resize)
        
        self.zoom_master.pack_propagate(True)
        self.zoom_frame = tk.Frame(self.zoom_master, bd=0, **fr)
        self.zoom_frame.pack(fill=tk.BOTH, expand=tk.YES, side=tk.LEFT) #,padx=10, pady=10 )

        self.canvas2 = FigureCanvasTkAgg(self.zoom_fig, master=self.zoom_frame)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        self.canvas2.get_tk_widget().configure(bg='black', highlightbackground="black", bd=0, ) 
        
        self.showing_zoom_window = True
    
    def line_select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self._set_zoom_img_slice( x1,x2,y1,y2, resize_zoom_window=True)

    def _set_zoom_img_slice(self,x1,x2,y1,y2, resize_zoom_window=False):
        self.zoom_ax.set_xlim(x1,x2)
        self.zoom_ax.set_ylim(y2,y1)
        
        if resize_zoom_window:
            width  = int(  (x2-x1)  / self.scale)
            height = int(  (y2-y1)  / self.scale)
            self._update_zoom_master_windowsize( width, height)
        
    def _update_zoom_master_windowsize(self, width, height):
        self.zoom_master.geometry("%dx%d" %( int(width), int(height)))
    
    def _setup_selector(self):
        self.RS = RectangleSelector(self.ax, self.line_select_callback,
                                       drawtype='box', useblit=0,
                                       button=[1, 3],  
                                       minspanx=10, minspany=10,
                                       spancoords='data',
                                       interactive=True,
                                       rectprops=self.rectprops)

    


if __name__ == '__main__':
    img = np.random.random(  (1500,1500) )
    Y,X = np.indices( (1500,1500))
    img = np.sin(X**2/ 10000.)**2 *np.cos(Y**2/10000.)*3

    root = tk.Tk()
    im = ImageViewer(root, img, background='black')
    im.pack(fill=tk.BOTH, expand=tk.YES)
    
    root.mainloop()




