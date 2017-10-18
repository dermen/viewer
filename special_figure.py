import Tkinter as tk
import matplotlib as mpl
mpl.use('TkAgg')
import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
from matplotlib.widgets import RectangleSelector


class Formatter(object):
    def __init__(self, im):
        self.im = im
    def __call__(self, x, y):
        z = self.im.get_array()[int(y), int(x)]
        return 'x={:.0f}, y={:.0f}, z={:.01f}'.format(x, y, z)

class ImageViewer(tk.Frame):
    
    def __init__(self, master, img_data,  *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.master = master
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
            vmin=None, vmax=None)
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
        self.frame12 = tk.Frame(self.master)
        self.frame12.pack(fill=tk.BOTH, side=tk.LEFT, expand=1)
        
        self.use_rect_zoom_var = tk.IntVar()
        self.use_rect_zoom_checkbutton = tk.Checkbutton(self.frame12, text='Rectangle zoom', 
            var=self.use_rect_zoom_var, command=self._set_rectangle_zoom)
        self.use_rect_zoom_checkbutton.pack(side=tk.TOP)

        self.frame1 = tk.Frame(self.frame12)
        self.frame1.pack(fill=tk.BOTH, expand=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame1)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.frame2 = tk.Frame(self.frame12)
        self.frame2.pack(fill=tk.X, expand=0)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame2)
        #self.toolbar = CustomToolbar(self.canvas, self.frame2)
        self.toolbar.update()
        self.toolbar.pack(fill=tk.X, expand=0)
    

    def _setup_zoom_space(self):
        self.zoom_fig = plt.figure(2)
        self.zoom_ax = self.zoom_fig.add_axes([0,0,1,1])
        self.zoom_ax.axis('off')
        self.zoom_fig.patch.set_visible(False)
        self.zoom_fig.canvas.toolbar.pack_forget()

        self.frame3 = tk.Frame(self.master)
        self.frame3.pack(fill=tk.BOTH, expand=1, side=tk.LEFT)

        self.var = tk.IntVar()
        self.cb = tk.Checkbutton(self.frame3, text='Show pixel values', 
            variable=self.var, command=self._toggle_show_pixel_values)
        self.cb.pack(side=tk.TOP)

        self.canvas2 = FigureCanvasTkAgg(self.zoom_fig, master=self.frame3)
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
        self.zoom_ax.imshow( self.img2, aspect='auto', interpolation='nearest')
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
    im = ImageViewer(root, img)
    im.pack(fill=tk.BOTH, expand=1)
    root.mainloop()

