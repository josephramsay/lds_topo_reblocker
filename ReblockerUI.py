'''
Created on 17/12/2015

@author: jramsay
'''
        
import os
import sys
import logging     

#from KPCInterface import KPCUploader as KU

THISF = os.path.normpath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(THISF,'../LDS/LDSAPI')))
#sys.path.append(os.path.abspath("../LDSAPI"))

from KPCInterface import KPCUploader as KU

import LayerReader as LR

PYVER3 = sys.version_info > (3,)

#2 to 3 imports
if PYVER3:
    import tkinter as TK
    from tkinter.scrolledtext import ScrolledText
    from tkinter.constants import FLAT,RAISED,SUNKEN,TOP,BOTTOM,RIGHT,LEFT,BOTH,END,X,Y,W,E,N,S,ACTIVE  
    import tkinter.filedialog as FD
else:
    import Tkinter as TK 
    from ScrolledText import ScrolledText
    from Tkconstants import FLAT,RAISED,SUNKEN,TOP,BOTTOM,RIGHT,LEFT,BOTH,END,X,Y,W,E,N,S,ACTIVE  
    import tkFileDialog as FD
    pass
    
# "hcieposd:l:u:m:wvnxyrz", 
["help","cropregion","import","export","process","overwrite","selection", \
"dir=","layer=","ufid=","merge=","webservice","version","nolaunder","excise","deepexcise","release","linkrelease"]    

'''
usage: python LayerReader [-h|--help]|[-c|--cropregion][-i|--import][-e|--export][-p|--process]
            [-d|--dir </shapefile/dir>][-s|--select][-l|--layer <layername>][-o|--overwrite]
            [-u|--ufid <primary-key>][-m|--merge <primary-key>][-w|--webservice][-v|--version]
            [-x/-excise][-y/--deepexcise][-r/--release][-z/--linkrelease]
-h/--help : Print out this help message
-c/--cropregion : Reload auxilliary map files 
    i.e. CropRegions to subdivide area and utilise less memory when processing
-i/--import : Run Shape to PostgreSQL Only
-e/--export : Run PostgreSQL to Shape Only
-p/--process : Run Reblocking process Only
-o/--overwrite : Overwrite (imported and reblocked tables)
-s/--selection : Only process and export layers found in the import directory
-d/--dir <path> : Specifiy a shapefile import directory
-l/--layer <layer> : Specify a single layer to import/process/export
-u/--ufid <ufid> : Specify the name of the primary key field for a layer/set-of-layers 
    e.g. t50_fid/t250_fid
-m/--merge <ufid> : Returns the layers using this composite ID and its components
-w/--webservice : Enable Webservice lookup for missing EPSG
-v/--version : Enable table versioning
-x/--excise : Remove named column from output shapefile
-y/--deepexcise : Remove named column from output shapefile (including all subdirectories)
-r/--release : Release reblocking data to topo_rdb
-z/--linkrelease : Link and Release reblocking data to topo_rdb
'''


#ADD 
#1.Reload_Index option to fetch new list of layers
if os.name =='posix':
    DEF_PATH = '/home/jramsay/temp/toposhp/bp'
else: 
    DEF_PATH = 'C:\\Data\\'

DEF_UFID = 't50_fid'
DEF_GID = 0 # option 0
LOGCOUNT = 0

class WidgetLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.widget = widget

    def emit(self, record):
        # Append message (record) to the widget
        global LOGCOUNT
        LOGCOUNT += 1
        print ('REC',LOGCOUNT,record)
        self.widget.insert(TK.INSERT, '[{}]  {}\n'.format(LOGCOUNT,record))
        self.widget.update()

class RUI(object):
    
    #dirname = os.path.dirname(__file__)
    dirname = DEF_PATH
    
    def __init__(self, master=None):
        self.master = TK.Tk()
        self.master.wm_title('ReblockerUI')
        
        self.menubar = TK.Menu(self.master)

        self.buttonframe  = TK.Frame(self.master,height=10,width=100,bd=2,relief=FLAT)
        self.controlframe = TK.Frame(self.master,height=20,width=100,bd=2,relief=FLAT)
        self.inputframe   = TK.Frame(self.controlframe,height=20,width=50, bd=2,relief=FLAT)
        self.checkframe   = TK.Frame(self.controlframe,height=20,width=50, bd=2,relief=FLAT)
        self.logframe     = TK.Frame(self.master,height=80,width=100, bd=2,relief=SUNKEN)    
        
        self.buttonframe.pack(fill=X,side=BOTTOM)
        self.controlframe.pack(fill=X)
        self.inputframe.pack(side=LEFT,fill=BOTH)
        self.checkframe.pack(side=RIGHT)
        self.logframe.pack(fill=X,side=TOP)
        
        self.initMenus()
        self.initWidgets()
        self._offset(self.master)
        self.master.config(menu=self.menubar)
        self.master.mainloop()

    def initMenus(self):
        filemenu = TK.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Select", command=self.select)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="File", menu=filemenu)
        
        actionmenu = TK.Menu(self.menubar, tearoff=0)
        actionmenu.add_command(label="Reblock", command=self.reblock)
        self.menubar.add_cascade(label="Action", menu=actionmenu)
        
    def initWidgets(self):
        button_row = 0
        button_col = 0
        log_row = 5
        input_row = 0
        group_options = sorted(KU.SOURCE_DEFS.keys(),reverse=True)
        
        #B U T T O N        
        self.buttonframe.selectbt = TK.Button(self.buttonframe,  text='Select',  command=self.select)
        self.buttonframe.selectbt.grid( row=button_row,column=button_col+0,sticky=E)
  
        self.buttonframe.reblockbt = TK.Button(self.buttonframe, text='Reblock', command=self.reblock)
        self.buttonframe.reblockbt.grid(row=button_row,column=button_col+1,sticky=E)
 
        self.buttonframe.uploadbt = TK.Button(self.buttonframe,  text='Upload',  command=self.upload)
        self.buttonframe.uploadbt.grid( row=button_row,column=button_col+2,sticky=E)
 
        self.buttonframe.releasebt = TK.Button(self.buttonframe, text='Release', command=self.release)
        self.buttonframe.releasebt.grid(row=button_row,column=button_col+3,sticky=E)

        self.buttonframe.removebt = TK.Button(self.buttonframe, text='Remove',  command=self.remove)
        self.buttonframe.removebt.grid( row=button_row,column=button_col+4,sticky=E)
 
        self.buttonframe.quitbt = TK.Button(self.buttonframe,    text='Quit',    command=self.quit)
        self.buttonframe.quitbt.grid(   row=button_row,column=button_col+5,sticky=E)

  
        #C H E C K B O X
        self.checkframe.cblabel = TK.Label(self.checkframe,text='Options').grid(row=0,column=0,sticky=W)
        crcbv = TK.IntVar()
        self.checkframe.crcb = TK.Checkbutton(self.checkframe, text='Crop Region',variable=crcbv,selectcolor='grey')
        self.checkframe.crcb.grid(row=1,column=0,columnspan=2,sticky=W)
        self.checkframe.crcbvar = crcbv   
        owcbv = TK.IntVar()
        self.checkframe.owcb = TK.Checkbutton(self.checkframe, text='Overwrite',variable=owcbv,selectcolor='grey')
        self.checkframe.owcb.grid(   row=2,column=0,columnspan=2,sticky=W)
        self.checkframe.owcb.select()
        self.checkframe.owcbvar = owcbv   
        lrcbv = TK.IntVar()
        self.checkframe.lrcb = TK.Checkbutton(self.checkframe, text='Link Release',variable=lrcbv,selectcolor='grey')
        self.checkframe.lrcb.grid(row=3,column=0,columnspan=2,sticky=W)
        self.checkframe.lrcbvar = lrcbv
        ulcbv = TK.IntVar()
        self.checkframe.ulcb = TK.Checkbutton(self.checkframe, text='Update LDS Layers',variable=ulcbv,selectcolor='grey')
        self.checkframe.ulcb.grid(row=4,column=0,columnspan=2,sticky=W)
        self.checkframe.ulcbvar = ulcbv   
        
        #I N P U T

        self.inputframe.fidlb = TK.Label(self.inputframe,    text='UFID Column Name')   .grid(row=0,column=0,sticky=W)
        fidebv = TK.StringVar()
        fidebv.set(DEF_UFID)
        self.inputframe.fideb = TK.Entry(self.inputframe,textvariable=fidebv)
        self.inputframe.fideb.grid(row=input_row+0,column=1,columnspan=3)
        self.inputframe.fidebvar = fidebv
        
        self.inputframe.exciselb = TK.Label(self.inputframe, text='Column To Remove')   .grid(row=1,column=0,sticky=W)
        exciseebv = TK.StringVar()
        self.inputframe.exciseeb = TK.Entry(self.inputframe,textvariable=exciseebv)
        self.inputframe.exciseeb.grid(row=input_row+1,column=1,columnspan=3)
        self.inputframe.exciseebvar = exciseebv
        
        self.inputframe.dirlb = TK.Label(self.inputframe,    text='Shapefile Directory').grid(row=2,column=0,sticky=W)   
        direbv = TK.StringVar()
        direbv.set(DEF_PATH)#self.dirname)
        self.inputframe.direb = TK.Entry(self.inputframe,textvariable=direbv)
        self.inputframe.direb.grid(row=input_row+2,column=1,columnspan=3)
        self.inputframe.direbvar = direbv
           
        self.inputframe.gidlb = TK.Label(self.inputframe,    text='LINZ Org/Group')     .grid(row=3,column=0,sticky=W)      
        gidddv = TK.StringVar()
        gidddv.set(group_options[DEF_GID])
        self.inputframe.giddd = TK.OptionMenu(self.inputframe,gidddv,*group_options)
        self.inputframe.giddd.config(width=16)
        self.inputframe.giddd.grid(row=input_row+3,column=1,columnspan=3)
        self.inputframe.gidddvar = gidddv
        
        #T E X T L O G
        self.logframe.logwindow = ScrolledText(self.logframe)
        self.logframe.logwindow.config(bg='white',fg='black',relief=SUNKEN,wrap=TK.WORD)
        self.logframe.logwindow.grid(row=log_row,column=0,columnspan=6,rowspan=4)
        self.logger = WidgetLogger(self.logframe.logwindow)

        
    def quit(self):
        self.master.quit()
        
    def reblock(self):
        self.dirname = self.inputframe.direbvar.get()
        ufid = self.inputframe.fidebvar.get()
        lcr = self.checkframe.crcbvar.get()>0 or False
        ow = self.checkframe.owcbvar.get()>0 or False
        self.logger.emit('Reblock {} ufid={}, lcr={}, overwrite={}'.format(self.dirname,ufid,lcr,ow)) 
        #layer set to None since never used and acts as filter
        #actionflag set to 7=import/process/export, selectflag set to True = only process shp in dir
        LR.setOverwrite(ow)
        LR.convert(self.dirname,None,ufid,7,True,lcr)
        
    def upload(self):
        '''Single layer uploader'''
        self.dirname = self.inputframe.direbvar.get()
        grp = self.inputframe.gidddvar.get()
        self.logger.emit('Upload dir {} to {} DS'.format(self.dirname,grp))
        for fg in self._filter():
            fg = '{}{}{}'.format(self.dirname,os.path.sep,fg)
            print ('Uploading layer {}'.format(fg))    
            ldsup = KU.LDSUploader(self.logger,self.checkframe.owcbvar.get()>0 or False,self.checkframe.ulcbvar.get()>0 or False)
            ldsup.setLayer(fg)
            ldsup.setGroup(grp)
            ldsup.upload()
        
    def release(self):
        self.logger.emit('Release')
        print ('Releasing new topo release locally to CP witk linkrelease={}'.format(self.checkframe.lrcbvar.get()))
        #LR.release(link=self.checkframe.lrcbvar.get())
        
    def remove(self):
        fid = self.inputframe.fidebvar.get()
        self.logger.emit('Remove column lease'.format(fid))
        print ('Removing column from dir {} with cname {}'.format(self.dirname,fid))
        if True:#pass
            LR.deepcrop(self.dirname,fid)
        else:#pass
            LR.crop(self.dirname,fid)
    
    def select(self):
        self.dirname = self.dirname or DEF_PATH
        self.dirname = FD.askdirectory(parent=self.inputframe,initialdir=self.dirname,title='Please select a directory')
        self.inputframe.direbvar.set(self.dirname)
        #self.inputframe.direb.insert(0,self.dirname)
        print (self.dirname)
        self.logger.emit('Select {}'.format(self.dirname))
        
        #fdlg = FD.LoadFileDialog(self.inputframe, title="Choose A ShapeFile")#,filetypes=[('Shapefile','*.shp'),])
        #self.filename = fdlg.go(pattern='*.shp') # opt args: dir_or_file=os.curdir, pattern="*", default="", key=None)
       
    def _filter(self):
        '''filter list of files in selected directory with shape suffixes
        eg f1.shp,f1.shx,f1.prj,f1,cpg,f2.shp,f2.shx,f2.prj,f2,cpg,'''
        return set([fg[:fg.rfind('.')] for fg in os.listdir(self.dirname) if fg[fg.rfind('.')+1:] in KU.SHP_SUFFIXES])
        
    def _offset(self,window):
        window.update_idletasks()
        w = window.winfo_screenwidth()
        h = window.winfo_screenheight()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x = w/4 - size[0]/2
        y = h/4 - size[1]/2
        window.geometry("%dx%d+%d+%d" % (size + (x, y)))
    
    def _centre(self,window):
        '''_centre's window in middle of screen, sucks for dual monitors'''
        window.update_idletasks()
        w = window.winfo_screenwidth()
        h = window.winfo_screenheight()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        window.geometry("%dx%d+%d+%d" % (size + (x, y)))



def main():
    rui = RUI()
    #basic.mainloop()
    
    #ldsu = LDSUploader()
    #ldsu.upload()
    
    #quickstartexamples(ldsu)
            
if __name__ == '__main__':
    main()       
    