import Tkinter as tk
import matplotlib as mpl
mpl.use('TkAgg')
import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
from matplotlib.widgets import RectangleSelector

from new_slide_hist import HistUpdater

plt.style.use('dark_background')

fr = {'bg':'black'} 

class Formatter(object):
    def __init__(self, im):
        self.im = im
    def __call__(self, x, y):
        z = self.im.get_array()[int(y), int(x)]
        return 'x={:.0f}, y={:.0f}, z={:.01f}'.format(x, y, z)

class ZoomPan:
    def __init__(self):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None


    def zoom_factory(self, ax, base_scale = 2.):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1
                print event.button

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)

        return zoom

    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            self.cur_xlim = ax.get_xlim()
            self.cur_ylim = ax.get_ylim()
            self.press = self.x0, self.y0, event.xdata, event.ydata
            self.x0, self.y0, self.xpress, self.ypress = self.press

        def onRelease(event):
            self.press = None
            ax.figure.canvas.draw()

        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            dx = event.xdata - self.xpress
            dy = event.ydata - self.ypress
            self.cur_xlim -= dx
            self.cur_ylim -= dy
            ax.set_xlim(self.cur_xlim)
            ax.set_ylim(self.cur_ylim)

            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest

        # attach the call back
        fig.canvas.mpl_connect('button_press_event',onPress)
        fig.canvas.mpl_connect('button_release_event',onRelease)
        fig.canvas.mpl_connect('motion_notify_event',onMotion)

        #return the function
        return onMotion







class ImageViewer(tk.Frame):
    
    def __init__(self, master, img_data,  *args, **kwargs):
        tk.Frame.__init__(self, master,  background='black') #*args, **kwargs)
        self.master = master
        
        self.image_frame = tk.Frame( self.master, **fr )
        self.image_frame.pack( side=tk.TOP)
        
        self.slider_frame = tk.Frame(self.master, **fr)
        self.slider_frame.pack(side=tk.TOP, expand=1, fill=tk.BOTH)
        self.hist_frame = tk.Frame( self.slider_frame , **fr)
        self.hist_frame.pack( side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.vmin = self.vmax = None

        #load the image
        self.img = img_data
        self.rectprops = dict(facecolor='red', edgecolor = 'black',
                 alpha=0.2, fill=True)
        
        self._create_figure()    
        self._add_img()
        self._setup_canvas()
        self.show_pixel_values=False
        self._setup_zoom_space()
        self._setup_selector()
        self.ymin = None
        self.RS.set_active(False)
        self.toggle_tools()
        self._zoom_im = None

        self._add_hist_updater()

        self._update_clim()

    def _update_clim(self):
        self.vmin, self.vmax = self.hist_updater.minval, self.hist_updater.maxval
        self._im.set_clim( vmin=self.vmin, vmax=self.vmax)
        if self._zoom_im is not None:
            self._zoom_im.set_clim( vmin=self.vmin, vmax=self.vmax)
        self.canvas.draw()
        self.canvas2.draw()
        self.master.after( 500, self._update_clim )    

    def _add_hist_updater(self):
        self.hist_updater = HistUpdater( self.hist_frame, self.img.ravel(), label='pixels', plot=False, range_slider_len=800, 
            background='black')
        self.hist_updater.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        
    def toggle_tools(self):
        if self.toolbar._active in ['PAN','ZOOM']:
            self.use_rect_zoom_var.set(0)
            self.RS.set_active(False)
        self.master.after( 100, self.toggle_tools )

    def _create_figure(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        
        self.ax.set_aspect('equal')
        self.fig.patch.set_visible(False)
        self.ax.axis('off')
    
    def _add_img(self):
        self._im = self.ax.imshow(self.img, aspect='equal', interpolation='nearest', norm=None, 
            vmin=self.vmin, vmax=self.vmax, cmap='gnuplot')
        self.vmin,self.vmax = self._im.get_clim()
        #self.cbar = plt.colorbar( self._im)
        self.ax.format_coord = Formatter(self._im)

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

    def _setup_canvas(self):
        self.image_frame_left = tk.Frame(self.image_frame, **fr)
        self.image_frame_left.pack(fill=tk.BOTH, side=tk.LEFT, expand=1)
        
        self.use_rect_zoom_var = tk.IntVar()
        self.use_rect_zoom_checkbutton = tk.Checkbutton(self.image_frame_left, text='Rectangle zoom', 
            var=self.use_rect_zoom_var, command=self._set_rectangle_zoom, fg='white', bg='black')
        self.use_rect_zoom_checkbutton.pack(side=tk.TOP)

        self.image_left_canvas_frame = tk.Frame(self.image_frame_left, **fr)
        self.image_left_canvas_frame.pack(fill=tk.BOTH, expand=1)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.image_left_canvas_frame)
        self.canvas.get_tk_widget().configure(background='black', highlightcolor='black', highlightbackground='black')
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.image_toolbar_fr = tk.Frame(self.image_frame_left, **fr)
        self.image_toolbar_fr.pack(fill=tk.X, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.image_toolbar_fr)
        self.toolbar.update()
        #self.toolbar.get_tk_widget().configure(background='black', highlightcolor='black', highlightbackground='black')
        self.toolbar.pack(fill=tk.X, expand=1)
        
        self.zp = ZoomPan()
        self.figZoom = self.zp.zoom_factory( self.ax, base_scale=1.1)
    

    def _setup_zoom_space(self):
        self.zoom_fig = plt.figure(2)
        self.zoom_ax = self.zoom_fig.add_axes([0,0,1,1])
        self.zoom_ax.axis('off')
        self.zoom_fig.patch.set_visible(False)
        self.zoom_fig.canvas.toolbar.pack_forget()

        self.zoom_frame = tk.Frame(self.image_frame, **fr)
        self.zoom_frame.pack(fill=tk.BOTH, expand=1, side=tk.LEFT,padx=10, pady=10 )

        self.var = tk.IntVar()
        self.cb = tk.Checkbutton(self.zoom_frame, text='Show pixel values', 
            variable=self.var, command=self._toggle_show_pixel_values, fg='white', bg='black')
        self.cb.pack(side=tk.TOP)

        self.canvas2 = FigureCanvasTkAgg(self.zoom_fig, master=self.zoom_frame)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    def _toggle_show_pixel_values(self,):
        self.show_pixel_values = self.var.get()
        if self.ymin is not None:
            self._draw_zoom()
    
    def line_select_callback(self, eclick, erelease):
        'eclick and erelease are the press and release events'
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        self.ymin = int( min(y1,y2) )
        self.ymax = int( max(y1,y2) )
        self.xmin = int( min(x1,x2) )
        self.xmax = int( max(x1,x2) )
        self.img2 = self.img[  self.ymin: self.ymax, self.xmin: self.xmax]
        self._draw_zoom()

    def _draw_zoom(self):
        self.zoom_ax.clear()
        self._zoom_im = self.zoom_ax.imshow( self.img2, aspect='auto', 
            interpolation='nearest', vmin=self.vmin, vmax=self.vmax, cmap='gnuplot')
        if self.show_pixel_values and self.img2.size < 1000:
            for y in range(self.img2.shape[0]):
                for x in range(self.img2.shape[1]):
                    self.zoom_ax.text(x , y , '%.1f' % self.img2[y, x],
                         horizontalalignment='center',
                         verticalalignment='center',)
   
        self.canvas2.draw()

    def _setup_selector(self):
        self.RS = RectangleSelector(self.ax, self.line_select_callback,
                                       drawtype='box', useblit=0,
                                       button=[1, 3],  
                                       minspanx=2, minspany=2,
                                       spancoords='data',
                                       interactive=True,
                                       rectprops=self.rectprops)


if __name__ == '__main__':
    img = np.random.random(  (1500,1500) )
    Y,X = np.indices( (1500,1500))
    img = np.sin(X**2/ 10000.)**2 *np.cos(Y**2/10000.)*3
    
    root = tk.Tk()
    im = ImageViewer(root, img, background='black')
    im.pack(fill=tk.BOTH, expand=1)
    root.mainloop()

