try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import numpy as np


labstyle={'bg':'black', 'fg':'white'}

fr = {'bg':'black'}
frpk = {'padx':0, 'pady':0}




class RangeSlider(tk.Frame):
    def __init__(self, parent, data, color='#00fa32', 
            length=600, height=50,**kwargs):
       
        tk.Frame.__init__(self, parent,  background='black') #**kwargs)
        
        self.color = color

        self.dat = data
        m = data.mean()
        s = data.std()
        self.minval = m - 1*s
        self.maxval = m + 4*s

        self.Ndat = len(self.dat)
        self.dmax = max( self.dat)
        self.dmin = min(self.dat)
        self.holding_master = False

#       frames
        self.container_frame = tk.Frame( self, **fr)
        self.container_frame.pack(side=tk.TOP, expand=tk.YES, **frpk)
        self.slider_frame = tk.Frame(self.container_frame, **fr)
        self.slider_frame.pack(side=tk.TOP, expand=tk.YES, **frpk)
        
        self.range_slider_len = length
        self.range_slider_height= height
        
        self._set_item_sizes()

        
######################
#       INIT METHODS
        self._drag_data = {"x": 0, "y": 0, "item": None}
        self._create_canvas()
        self._create_slider_track()
        self._create_slider_handles()
        self._create_handle_labels()
        self._bind_slider_handles()
        
        self.master.bind("<Configure>", self._on_resize_master)
        self.master.bind("<Button-1>", self._on_click_master)
        self.master.bind("<ButtonRelease-1>", self._on_release_master)

    #       ATTRIBS
    
    def _set_item_sizes(self):        
        
        self.LHS_textY=15/60. * self.range_slider_height
        self.RHS_textY=40/60. * self.range_slider_height
        self.token_height=30/60.*self.range_slider_height
        
        self.y_offset = 10/60.*self.range_slider_height
        self.token_width = 30/600.*self.range_slider_len
        self.LHS_gap = 30/600.*self.range_slider_len
        self.RHS_gap = 30/600.*self.range_slider_len
        self.text_offset = 7.5/600.*self.range_slider_len
        self.xmax = self.range_slider_len - self.RHS_gap
        self.xmin = self.LHS_gap
        self.line_pos = self.range_slider_height/2.
        self.slider_range = self.xmax -  self.xmin
    
        self.fontsize = int( self.token_width*0.75 )

    def _on_click_master(self, event):
        print("clicked master")
        self.holding_master = True
         
    def _on_release_master(self, event):
        print("released master") 
        self.holding_master = False

    def _on_resize_master(self, event):
        if self.holding_master:
            wscale = float(event.width)/self.range_slider_len
            hscale = float(event.height)/self.range_slider_height
            
            self.range_slider_len = event.width
            self.range_slider_height = event.height
            self.canvas.config(width=event.width, height=event.height)
           
#           resize slider handles
            scale_order = [wscale, hscale, wscale, hscale, wscale, hscale]
            token_coor = self.canvas.coords( self.items[0])
            token_coor_new = [ i*scale for i,scale in zip( token_coor, scale_order)]
            self.canvas.coords( self.items[0], *token_coor_new)

            token_coor = self.canvas.coords( self.items[1])
            token_coor_new = [ i*scale for i,scale in zip( token_coor, scale_order)]
            self.canvas.coords( self.items[1], *token_coor_new)

#           resize slider track
            line_coor = self.canvas.coords( "track")
            scale_order = [ wscale, hscale, wscale, hscale]
            line_coor_new = [ i*scale for i,scale in zip( line_coor, scale_order)]
            self.canvas.coords( "track", *line_coor_new)

#           reposition slider text
            scale_order = [wscale, hscale]
            text_coor = self.canvas.coords("mintext")
            text_coor_new = [ i*scale for i,scale in zip( text_coor, scale_order)]
            self.canvas.coords( "mintext", *text_coor_new)
            

            
            text_coor = self.canvas.coords("maxtext")
            text_coor_new = [ i*scale for i,scale in zip( text_coor, scale_order)]
            self.canvas.coords( "maxtext", *text_coor_new)
            
            self._set_item_sizes()
            
            new_font_size =  int( self.token_width  * .75)
            new_font = "Helvetica %d"%new_font_size
            self.canvas.itemconfig( "mintext", font=new_font)
            self.canvas.itemconfig( "maxtext", font=new_font)
            
    
    def _create_canvas(self):
        self.canvas = tk.Canvas(self.slider_frame, width=self.range_slider_len, 
            height=self.range_slider_height, bg='black', highlightthickness=1, 
            highlightbackground="white")
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH, **frpk)

    def _create_slider_track(self):
        self.canvas.create_line( ( self.LHS_gap, 
            self.line_pos,
            self.range_slider_len-self.RHS_gap, 
            self.line_pos), fill=self.color, width=1,tags="track")
        

    def _create_slider_handles(self):
#       create a couple of movable sliders
        
        coor1 = [  self.xmin-self.token_width*.5 , self.line_pos-self.token_height, 
             self.xmin+self.token_width*.5 , self.line_pos-self.token_height,
             self.xmin, self.line_pos  ]
        
        i1 = self.canvas.create_polygon( coor1, 
                activefill=self.color,
                outline=self.color, 
                fill="black", tags="token", width=2)
        
        coor2 = [  self.xmax-self.token_width*.5 , self.line_pos+self.token_height, 
             self.xmax+self.token_width*.5 , self.line_pos+self.token_height,
             self.xmax, self.line_pos  ]
        
        i2 = self.canvas.create_polygon( coor2, 
                activefill=self.color,
                outline=self.color, 
                fill="black", tags="token", width=2)
        
        self.items = [i1, i2] # store the IDs
       
    def _create_handle_labels(self):
        self.minvaltext = self.canvas.create_text( 
            self.xmin + self.token_width+self.text_offset, 
            self.LHS_textY, text="%.2f"%self.dmin, font=("Helvetica", self.fontsize), 
            fill='white', tags="mintext")
        self.maxvaltext = self.canvas.create_text( 
            self.xmax - self.token_width-self.text_offset,
            self.RHS_textY, text="%.2f"%self.dmax, fill='white', font=("Helvetica", self.fontsize),
            tags="maxtext")
       
    def _bind_slider_handles(self):
        # any object with the "token" tag
        self.canvas.tag_bind("token", "<ButtonPress-1>", self.on_token_press)
        self.canvas.tag_bind("token", "<ButtonRelease-1>", self.on_token_release)
        self.canvas.tag_bind("token", "<B1-Motion>", self.on_token_motion)
        
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
        clicked_coors = self.canvas.coords(clicked_item)
        _,_,_,_, clicked_x,_ = clicked_coors #xleft, ybottom, xright, ytop = coors
        
        #clicked_x = .5* (xleft + xright)
        
        other_item = [i for i in self.items if i != clicked_item][0]
        other_coors = self.canvas.coords(other_item)
        other_x = other_coors[4] #.5*(other_coors[0] + other_coors[2])
        
        if clicked_x > other_x:
            #   RIGHT HAND SIDE ITEM
            delta_x = event.x - self._drag_data["x"]
            x_new = min( clicked_x + delta_x, self.xmax) 
            x_new = max( x_new, other_x+0.00001)

            clicked_coors[4] = x_new
            clicked_coors[0] = x_new-self.token_width*.5
            clicked_coors[2] = x_new+ self.token_width*.5
            self.canvas.coords( clicked_item,*clicked_coors) 
            
            self.canvas.coords( self.maxvaltext, (x_new - self.token_width-self.text_offset,
                self.RHS_textY))
            
            new_drag = min( self.xmax,  event.x)
            new_drag = max(  other_x , new_drag)
            self._drag_data["x"] = new_drag 
            self.maxval = ( (x_new - self.xmin) / self.slider_range ) \
                * ( self.dmax - self.dmin ) + self.dmin
            self.canvas.itemconfig( self.maxvaltext, text="%.2f"%self.maxval)
            
        else:
            #   LEFT HAND SIDE ITEM
            delta_x = event.x - self._drag_data["x"]
            
            x_new = max( clicked_x + delta_x, self.xmin) 
            x_new = min( x_new, other_x-0.00001) #-self.token_width) 
            
            clicked_coors[4] = x_new
            clicked_coors[0] = x_new-self.token_width*.5
            clicked_coors[2] = x_new+ self.token_width*.5
            
            self.canvas.coords( clicked_item,*clicked_coors) 
            
            self.canvas.coords( self.minvaltext, (x_new+self.token_width+self.text_offset,
                self.LHS_textY))
            new_drag = max( self.xmin,  event.x)
            new_drag = min(  other_x , new_drag)
            self._drag_data["x"] = new_drag 
            
            self.minval = ( ( x_new-self.xmin ) / self.slider_range ) \
                * ( self.dmax - self.dmin ) + self.dmin
            
            self.canvas.itemconfig( self.minvaltext, text="%.2f"%self.minval)
        

def main():
    test_data = np.random.normal( 10,1,10000)
    test_data2 = np.random.normal( 0,2,10000)
    #test_data3 = np.random.normal( 10,1,10000)
    #test_data4 = np.random.normal( 50,5,10000)
    #test_data5 = np.random.normal( 10,1,10000)
    #test_data6 = np.random.normal( 50,5,10000)
    #DAT = [ test_data, test_data2, test_data3, test_data4, test_data5, test_data6]
    
    
    #colors = ['red', 'red', 'red', 'blue', 'blue', 'blue']
    
    root = tk.Tk()
    rangeslide = RangeSlider(root, test_data, color="#00fa32")
    rangeslide.pack( side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
    root.mainloop()


    
if __name__ == "__main__":
    main()
