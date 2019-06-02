#pragma rtGlobals=3		// Use modern global access method and strict wave access.

menu "YW"
submenu "Export"
	submenu ".arpy"
		"Export single wave", SingleWave_arpy()
  		"Export 1D wave with Scale", OneDWavewithScale_arpy()
  	end
	submenu ".ig2py"
  		"Export single wave", SingleWave_ig2py()
  		"Export 1D wave with Scale", OneDWavewithScale_ig2py()
	end
end
end

function SingleWave_arpy()
    variable idx=0
    string path
    string wavname, keynote
    variable i,j
    newpath/q/o/m="Choose the folder to save data." savetxtfolder
    pathinfo savetxtfolder
    path = S_path
    do
       wavname = GetBrowserSelection(idx)
       if(strlen(wavname) == 0)
          break
       else
          wave wref = $wavname
          variable refnum
          open refnum as path+nameofwave(wref)+".arpy"
          //print header
          string header="ARPY_FILE"
          string energyaxis
          keynote = stringbykey("energyAxis", note(wref), "=", "\r")
          if(strlen(keynote) > 0)
            energyaxis=keynote[0]
          else
            energyaxis="N"
          endif
          string spacemode
          keynote = stringbykey("spacemode", note(wref), "=", "\r")
          if(strlen(keynote) > 0)
            spacemode=keynote[0]
          else
            spacemode="N"
          endif
          fbinwrite/b=3/f=0 refnum, header
          fbinwrite/b=3/f=0 refnum, energyaxis
          fbinwrite/b=3/f=0 refnum, spacemode
          //print dimension
          variable dims = wavedims(wref)
          fbinwrite/b=3/f=3 refnum, dims
          variable xsize=dimsize(wref,0), ysize=dimsize(wref,1), zsize=dimsize(wref,2), tsize=dimsize(wref,3)
          fbinwrite/b=3/f=3 refnum, xsize
          fbinwrite/b=3/f=3 refnum, ysize
          fbinwrite/b=3/f=3 refnum, zsize
          fbinwrite/b=3/f=3 refnum, tsize
          //print scale
          make/n=(xsize)/o/D xscale
          xscale[] = dimoffset(wref,0)+p*dimdelta(wref,0)
          fbinwrite/b=3/f=5 refnum, xscale
          killwaves xscale
          if(dims > 1)
             make/n=(ysize)/o/D yscale
          	  yscale[] = dimoffset(wref,1)+p*dimdelta(wref,1)
             fbinwrite/b=3/f=5 refnum, yscale
             killwaves yscale
          endif
          if(dims > 2)
             make/n=(zsize)/o/D zscale
          	  zscale[] = dimoffset(wref,2)+p*dimdelta(wref,2)
             fbinwrite/b=3/f=5 refnum, zscale
             killwaves zscale
          endif
          if(dims > 3)
             make/n=(tsize)/o/D tscale
          	  tscale[] = dimoffset(wref,3)+p*dimdelta(wref,3)
             fbinwrite/b=3/f=5 refnum, tscale
             killwaves tscale
          endif
          //print data
          redimension/D wref
          fbinwrite/b=3/f=4 refnum, wref    //igor uses Fortran order: row first, column second, layer third
          //close file
          print "Export "+nameofwave(wref)
          close refnum
       endif
       idx+=1
    while(1)
end

function OneDWavewithScale_arpy()
end

function SingleWave_ig2py()
    variable idx=0
    string path
    string wavname
    variable i,j
    do
       wavname = GetBrowserSelection(idx)
       if(strlen(wavname) == 0)
          break
       else
          wave wref = $wavname
          newpath/q/o/m="Choose the folder to save data." savetxtfolder
          pathinfo savetxtfolder
          path = S_path
          variable refnum
          open refnum as path+nameofwave(wref)+".ig2py"
          //print header
          fprintf refnum, "#Igor to Python\n\n"
          fprintf refnum, "[Header]\n"
          fprintf refnum, "\"XMin\": \"%g\"\n", dimoffset(wref, 0)
          fprintf refnum, "\"XStep\": \"%g\"\n", dimdelta(wref, 0)
          fprintf refnum, "\"XMax\": \"%g\"\n", dimoffset(wref, 0)+(dimsize(wref, 0)-1)*dimdelta(wref, 0)
          switch(wavedims(wref))
          case 1:
             fprintf refnum, "\"YMin\": \"%g\"\n", 0
             fprintf refnum, "\"YStep\": \"%g\"\n", 0
             fprintf refnum, "\"YMax\": \"%g\"\n", 0
             fprintf refnum, "\"ZMin\": \"%g\"\n", 0
             fprintf refnum, "\"ZStep\": \"%g\"\n", 0
             fprintf refnum, "\"ZMax\": \"%g\"\n", 0
             fprintf refnum, "\"Dimension\": \"(%g,)\"\n", dimsize(wref, 0)
          case 2:
             fprintf refnum, "\"YMin\": \"%g\"\n", dimoffset(wref, 1)
             fprintf refnum, "\"YStep\": \"%g\"\n", dimdelta(wref, 1)
             fprintf refnum, "\"YMax\": \"%g\"\n", dimoffset(wref, 1)+(dimsize(wref, 1)-1)*dimdelta(wref, 1)
             fprintf refnum, "\"ZMin\": \"%g\"\n", 0
             fprintf refnum, "\"ZStep\": \"%g\"\n", 0
             fprintf refnum, "\"ZMax\": \"%g\"\n", 0
             fprintf refnum, "\"Dimension\": \"(%g, %g)\"\n", dimsize(wref, 0), dimsize(wref, 1)
          break
          case 3:
             fprintf refnum, "\"YMin\": \"%g\"\n", dimoffset(wref, 1)
             fprintf refnum, "\"YStep\": \"%g\"\n", dimdelta(wref, 1)
             fprintf refnum, "\"YMax\": \"%g\"\n", dimoffset(wref, 1)+(dimsize(wref, 1)-1)*dimdelta(wref, 1)
             fprintf refnum, "\"ZMin\": \"%g\"\n", dimoffset(wref, 2)
             fprintf refnum, "\"ZStep\": \"%g\"\n", dimdelta(wref, 2)
             fprintf refnum, "\"ZMax\": \"%g\"\n", dimoffset(wref, 2)+(dimsize(wref, 2)-1)*dimdelta(wref, 2)
             fprintf refnum, "\"Dimension\": \"(%g, %g, %g)\"\n", dimsize(wref, 0), dimsize(wref, 1), dimsize(wref, 2)
          break
          endswitch
          string keywords = "energyAxis;spacemode;"
          string key, keynote
          for(i=0;i<itemsinlist(keywords);i+=1)
            key = stringfromlist(i, keywords)
            keynote = stringbykey(key, note(wref), "=", "\r")
            if(strlen(keynote) > 0)
             	fprintf refnum, "\""+key+"\": \"%s\"\n", keynote
            endif
          endfor
          //print scale
          fprintf refnum, "\n[Scale]\n"
          for(i=0;i<dimsize(wref,0);i+=1)
             fprintf refnum, "%g\t", dimoffset(wref,0)+i*dimdelta(wref,0)
          endfor
          fprintf refnum, "\n"
          if(wavedims(wref) > 1)
             for(i=0;i<dimsize(wref,1);i+=1)
                fprintf refnum, "%g\t", dimoffset(wref,1)+i*dimdelta(wref,1)
             endfor
          endif
          fprintf refnum, "\n"
          if(wavedims(wref) > 2)
             for(i=0;i<dimsize(wref,2);i+=1)
                fprintf refnum, "%g\t", dimoffset(wref,2)+i*dimdelta(wref,2)
             endfor
          endif
          fprintf refnum, "\n"
          //print data
          fprintf refnum, "\n[Data]\n"
          switch(wavedims(wref))
          case 1:
             wfprintf refnum, "%g\n"/R=[0,dimsize(wref,0)-1], wref
          break
          case 2:
             for(i=0;i<dimsize(wref,0);i+=1)
                make/o/n=(dimsize(wref,1)) tempw
                tempw[]=wref[i][p]
                wfprintf refnum, "%g\t"/R=[0,dimsize(tempw,0)-1], tempw
                fprintf refnum, "\n"
             endfor
             killwaves tempw
          break
          case 3:
             for(j=0;j<dimsize(wref,2);j+=1)
                for(i=0;i<dimsize(wref,0);i+=1)
                   make/o/n=(dimsize(wref,1)) tempw
                   tempw[]=wref[i][p][j]
                   wfprintf refnum, "%g\t"/R=[0,dimsize(tempw,0)-1], tempw
                   fprintf refnum, "\n"
                endfor
             endfor
             killwaves tempw
          break
          endswitch
          print "Export "+nameofwave(wref)
          close refnum 
       endif
       idx+=1
    while(1)
end

function OneDWavewithScale_ig2py()
end