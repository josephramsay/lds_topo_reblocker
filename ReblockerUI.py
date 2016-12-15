'''
Created on 17/12/2015

@author: jramsay
'''
        
import os
import sys
import logging     

from KPCInterface import KPCUploader as KU

import LayerReader as LR

PYVER3 = sys.version_info > (3,)

#2 to 3 imports
if PYVER3:
    import tkinter as TK
    import tkinter.scrolledtext as ScrolledText
    from tkinter.constants import RAISED,SUNKEN,BOTTOM,RIGHT,LEFT,END,X,Y,W,E,N,S,ACTIVE  
    import tkinter.filedialog as FD
else:
    #import Tkinter as TK 
    #from ScrolledText import ScrolledText
    #from Tkconstants import RAISED,SUNKEN,BOTTOM,RIGHT,LEFT,END,X,Y,W,E,N,S,ACTIVE  
    #2import tkFileDialog as FD
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
    DEF_PATH = '/home/jramsay/temp/toposhp/UITest/poly/sf_new'
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
        master = TK.Tk()
        master.wm_title('ReblockerUI')
        self.mainframe = TK.Frame(master,height=100,width=100,bd=1,relief=RAISED)
        #mainframe.__init__(self, master)
        self.mainframe.grid()
        self.initWidgets()
        self._offset(master)
        self.mainframe.mainloop()

    def initWidgets(self):
        button_row = 4
        log_row = 5
        group_options = sorted(KU.SOURCE_DEFS.keys(),reverse=True)
        #B U T T O N
        self.mainframe.selectbt = TK.Button(self.mainframe,  text='Select',  command=self.select)
        self.mainframe.selectbt.grid( row=button_row,column=0,sticky=E)
  
        self.mainframe.reblockbt = TK.Button(self.mainframe, text='Reblock', command=self.reblock)
        self.mainframe.reblockbt.grid(row=button_row,column=1,sticky=E)
 
        self.mainframe.uploadbt = TK.Button(self.mainframe,  text='Upload',  command=self.upload)
        self.mainframe.uploadbt.grid( row=button_row,column=2,sticky=E)
 
        self.mainframe.releasebt = TK.Button(self.mainframe, text='Release', command=self.release)
        self.mainframe.releasebt.grid(row=button_row,column=3,sticky=E)

        self.mainframe.removebt = TK.Button(self.mainframe, text='Remove',  command=self.remove)
        self.mainframe.removebt.grid( row=button_row,column=4,sticky=E)
 
        self.mainframe.quitbt = TK.Button(self.mainframe,    text='Quit',    command=self.quit)
        self.mainframe.quitbt.grid(   row=button_row,column=5,sticky=E)
  
        #C H E C K B O X
        crcbv = TK.IntVar()
        self.mainframe.crcb = TK.Checkbutton(self.mainframe, text='Crop Region',variable=crcbv)
        self.mainframe.crcb.grid( row=0,column=4,columnspan=2,sticky=W)
        self.mainframe.crcbvar = crcbv   
        owcbv = TK.IntVar()
        self.mainframe.owcb = TK.Checkbutton(self.mainframe, text='Overwrite',variable=owcbv)
        self.mainframe.owcb.grid(   row=1,column=4,columnspan=2,sticky=W)
        self.mainframe.owcb.select()
        self.mainframe.owcbvar = owcbv   
        lrcbv = TK.IntVar()
        self.mainframe.lrcb = TK.Checkbutton(self.mainframe, text='Link Release',variable=lrcbv)
        self.mainframe.lrcb.grid(row=2,column=4,columnspan=2,sticky=W)
        self.mainframe.lrcbvar = lrcbv   
        
        #L A B E L
        self.mainframe.fidlb = TK.Label(self.mainframe,    text='UFID Column Name').grid(  row=0,column=0,sticky=W)
        self.mainframe.exciselb = TK.Label(self.mainframe, text='Column To Remove').grid(  row=1,column=0,sticky=W)      
        self.mainframe.dirlb = TK.Label(self.mainframe,    text='Selected Directory').grid(row=2,column=0,sticky=W)      
        self.mainframe.gidlb = TK.Label(self.mainframe,    text='LINZ Group').grid(row=3,column=0,sticky=W)      
        
        #T E X T B O X
        fidebv = TK.StringVar()
        fidebv.set(DEF_UFID)
        self.mainframe.fideb = TK.Entry(self.mainframe,textvariable=fidebv)
        self.mainframe.fideb.grid(row=0,column=1,columnspan=3)
        self.mainframe.fidebvar = fidebv
        exciseebv = TK.StringVar()
        self.mainframe.exciseeb = TK.Entry(self.mainframe,textvariable=exciseebv)
        self.mainframe.exciseeb.grid(row=1,column=1,columnspan=3)
        self.mainframe.exciseebvar = exciseebv
        direbv = TK.StringVar()
        direbv.set(DEF_PATH)#self.dirname)
        self.mainframe.direb = TK.Entry(self.mainframe,textvariable=direbv)
        self.mainframe.direb.grid(row=2,column=1,columnspan=3)
        self.mainframe.direbvar = direbv
        
        #D R O P D O W N
        gidddv = TK.StringVar()
        gidddv.set(group_options[DEF_GID])
        self.mainframe.giddd = TK.OptionMenu(self.mainframe,gidddv,*group_options)
        self.mainframe.giddd.config(width=16)
        self.mainframe.giddd.grid(row=3,column=1,columnspan=3)
        self.mainframe.gidddvar = gidddv
        
        #T E X T L O G
        self.mainframe.logwindow = ScrolledText(self.mainframe)
        self.mainframe.logwindow.config(bg='white',relief=SUNKEN,wrap=TK.WORD)
        self.mainframe.logwindow.grid(row=log_row,column=0,columnspan=6,rowspan=4)
        self.logger = WidgetLogger(self.mainframe.logwindow)

        
    def quit(self):
        self.mainframe.quit()
        
    def reblock(self):
        self.dirname = self.mainframe.direbvar.get()
        ufid = self.mainframe.fidebvar.get()
        lcr = self.mainframe.crcbvar.get()>0 or False
        ow = self.mainframe.owcbvar.get()>0 or False
        self.logger.emit('Reblock {} ufid={}, lcr={}, overwrite={}'.format(self.dirname,ufid,lcr,ow)) 
        #layer set to None since never used and acts as filter
        #actionflag set to 7=import/process/export, selectflag set to True = only process shp in dir
        LR.setOverwrite(ow)
        LR.convert(self.dirname,None,ufid,7,True,lcr)
        
    def upload(self):
        '''Single layer uploader'''
        self.dirname = self.mainframe.direbvar.get()
        grp = self.mainframe.gidddvar.get()
        self.logger.emit('Upload dir {} to {} DS'.format(self.dirname,grp))
        for fg in self._filter():
            fg = '{}{}{}'.format(self.dirname,os.path.sep,fg)
            print ('Uploading layer {}'.format(fg))    
            ldsup = KU.LDSUploader(self.logger,self.mainframe.owcbvar.get()>0 or False)
            ldsup.setLayer(fg)
            ldsup.setGroup(grp)
            ldsup.upload()
        
    def release(self):
        self.logger.emit('Release')
        print ('Releasing new topo release locally to CP witk linkrelease={}'.format(self.mainframe.lrcbvar.get()))
        #LR.release(link=self.mainframe.lrcbvar.get())
        
    def remove(self):
        fid = self.mainframe.fidebvar.get()
        self.logger.emit('Remove column lease'.format(fid))
        print ('Removing column from dir {} with cname {}'.format(self.dirname,fid))
        if True:#pass
            LR.deepcrop(self.dirname,fid)
        else:#pass
            LR.crop(self.dirname,fid)
    
    def select(self):
        self.dirname = self.dirname or DEF_PATH
        self.dirname = FD.askdirectory(parent=self.mainframe,initialdir=self.dirname,title='Please select a directory')
        self.mainframe.direbvar.set(self.dirname)
        #self.mainframe.direb.insert(0,self.dirname)
        print (self.dirname)
        self.logger.emit('Select {}'.format(self.dirname))
        
        #fdlg = FD.LoadFileDialog(self.mainframe, title="Choose A ShapeFile")#,filetypes=[('Shapefile','*.shp'),])
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
    