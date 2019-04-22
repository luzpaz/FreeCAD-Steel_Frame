# -*- coding: utf-8 -*-
__Title__="Steel Frame Creator"
__Author__ = "Humberto Hassey, Beatriz Arellano"
__Version__ = "00.07"
__Date__    = "2017-12-27"
__Comment__ = "None"
__Web__ = "https://gitlab.com/Oriond/FreeCAD-Steel_Frame"
__Wiki__ = ""
__Icon__  = "/usr/lib/freecad/Mod/plugins/icons/Title_Of_macro"
__IconW__  = "C:/Documents and Settings/YourUserName/Application Data/FreeCAD"
__Help__ = "See Readme.MD on Gitlab"
__Status__ = "Experimental"
__Requires__ = "freecad 0.16"
__Communication__ = "https://forum.freecadweb.org/viewtopic.php?f=23&t=26092" 
import Part 
import FreeCAD
App=FreeCAD
#-------------------------------------------------------------------------------
def cortaStud(poste,ventana,zBeam,isFEMOff=True,isBeamOn=False,thick=0.001):
    '''this function takes a stud and a window and returns two studs resulting from
    substracting the window to the original stud or the same stud if no intersection is
    present'''
    listaStuds=[]
    if ventana[1]==0: #this is a door
        # Poste arriba puerta
        posX=poste[0]
        posZ=ventana[3]+thick*isFEMOff
        posSize=poste[2]-ventana[3]-2*thick*isFEMOff
        listaStuds.append((posX,posZ,posSize,poste[3]))
        return listaStuds
    elif ventana[1] >= poste[1]+poste[2]: #stud does not reach the window height
        listaStuds.append(poste)
        return listaStuds
    elif poste[1] > ventana[1]+ventana[3]: #Stud above window and does not cross window
        listaStuds.append(poste)
        return listaStuds
    elif  ventana[1]<poste[1]+poste[2]<ventana[1]+ventana[3]: #stud inside Structural beam
        hdown=ventana[1]-poste[1]+2*thick*(not(isFEMOff))
        posZ=poste[1]-thick*(not(isFEMOff))
        listaStuds.append((poste[0],posZ,hdown,poste[3]))
        return listaStuds
    else: # ventana[1]+ventana[3] < poste[1]+poste[2]: #stud passes the window height
        #poste debajo de ventana
        hdown=ventana[1]-poste[1]+2*thick*(not(isFEMOff))
        posZ=poste[1]-thick*(not(isFEMOff))
        listaStuds.append((poste[0],posZ,hdown,poste[3]))
        # Poste arriba ventana
        posX=poste[0]
        posZ=ventana[1]+ventana[3]-thick*(not(isFEMOff))
        posSize=poste[2]-ventana[3]-hdown+2*thick*(not(isFEMOff))
        listaStuds.append((posX,posZ,posSize,poste[3]))
        return listaStuds
#------------------------------------------------------------------------------   
        
def calcStuds(l,h,s,f,win,isFEMOff,pz0=0,isBeamOn=False,zBeam=0,thick=0):
    """
    Función que calcula la longitud de los postes a utilizar para un muro
    Recibe como parametros:
        -l: (float) longitud (x) del muro
        -h: (float) altura (z) del muro
        -s: (float) separación entre postes a lo largo del eje x
        -f: (float) longitud del "flange" del poste
        -win: lista de tuplas con la información de las ventanas, cada tupla es como sigue:
            (posición en x, posición en z, longitud en x, altura en z)        
        -pz0: (float) Posición inicial en z de los postes.
        -isBeamOn: (Boolean) If the structural option is selected or not
        -zBeam: Beam height
        
    Devuelve una lista de tuplas con la información de cada poste metálico:
        (px, pz, h, flipped):
            px: (float) posición a lo largo del eje x
            pz: (float) posición a lo largo del eje z
            h: (float) altura en z
            flipped: (boolean) indica si el poste va en posición invertida
    """
    def AddStud(x,pz0,h,flipped,stu):
        """
        Funcion que agrega los postes que enmarcan las ventanas y puertas.
        Si ya existe el poste en esa posición entonces no agrega uno más
        """
        if x not in [s[0] for s in stu]:
            stu.append((x,pz0,h,flipped)) #(px,pz,height,flipped)
        return stu    
    
    margen=2*f #Espacio mínimo entre dos postes
    studs=[]
    if 0 not in [w[0] for w in win]: #Verifica si hay una ventana o puerta en la arista inicial para girar o no el primer poste
        studs.append((0,pz0,h,False))
    for w in win:
        studs=AddStud(w[0],pz0,h,True,studs)
        studs=AddStud(w[0]+w[2],pz0,h,False,studs)        
        #***Verificar qué pasa si el poste que ya existe tiene otra orientación
        #***Verificar qué pasa si ese poste pasa por una puerta o ventana
    if l not in [w[0]+w[2] for w in win]:
        studs.append((l,pz0,h, True)) #Agrega el último poste verificando que no esté agregado aún como marco de puerta o ventana
    studs.sort(key=lambda tup: tup[0]) #Ordena a los postes por su posición en el eje x
    #Se agregan los postes intermedios que no forman parte de marcos
    notFrames=[] #Lista para agregar los postes que no son marcos
    for index, stu in enumerate(studs[1::]): #Comienza a iterar desde el segundo elemento de los postes        
        lBetFrames=stu[0]-studs[index][0]
        extra=0
        if lBetFrames%s >= margen:
            extra=1
        nStuds=int(lBetFrames/s)+extra        
        for ns in range(1,nStuds):
            notFrames.append((studs[index][0]+ns*s,pz0,h,False))
     
    studs+=notFrames
    # postes se defininen asi: (px, pz, h, flipped):
    ##********Cortar los postes que atraviesan ventanas y puertas
    copyWin=win[:]
    if isBeamOn: #If Structural, all Beams will be treated as windows to cut studs below them
        for w in win: 
            xmin=(w[0])
            xmax=( w[0]+w[2])
            copyWin.append((xmin,h-zBeam-1*thick,xmax-xmin,2*zBeam+1*thick*isFEMOff)) #2 por que quiero la ventana mas alta que los postes
    for w in copyWin:    #                     poste dentro de la ventana en x       
        interStuds = list(filter(lambda x: w[0]< x[0]< w[0]+w[2], studs))
        for iStu in interStuds:
            studs.remove(iStu)     
            studs.extend(cortaStud(iStu,w,zBeam,isFEMOff,isBeamOn,thick))
            
    studs.sort(key=lambda tup: tup[0])
    return studs
 #------------------------------------------------------------------------------  
   
def Draw_Steel_Stud(y,x,th1,z,falange=8,fliped =0):
    '''Author = Humberto Hassey
    Version=1.0
    Draw a Steel stud
    x=Width
    y=depth
    z=height
    Th1=steel thickness'
    Select Gauge=0 for custom thicknesses'''
    F=1
    if fliped ==1:
        F=-1
    # Vertices del stud
    V1=FreeCAD.Vector(0,0,0)
    V2=FreeCAD.Vector(x*F,0,0)
    V3=FreeCAD.Vector(x*F,falange,0)
    V4=FreeCAD.Vector((x-th1)*F,falange,0)
    V5=FreeCAD.Vector((x-th1)*F,th1,0)
    V6=FreeCAD.Vector(th1*F,th1,0)
    V7=FreeCAD.Vector(th1*F,y-th1,0)
    V8=FreeCAD.Vector((x-th1)*F,y-th1,0)
    V9=FreeCAD.Vector((x-th1)*F,y-falange,0)
    V10=FreeCAD.Vector(x*F,y-falange,0)
    V11=FreeCAD.Vector(x*F,y,0)
    V12=FreeCAD.Vector(0,y,0)

    #Lines
    L1=Part.makeLine(V1,V2)
    L2=Part.makeLine(V2,V3)
    L3=Part.makeLine(V3,V4)
    L4=Part.makeLine(V4,V5)
    L5=Part.makeLine(V5,V6)
    L6=Part.makeLine(V6,V7)
    L7=Part.makeLine(V7,V8)
    L8=Part.makeLine(V8,V9)
    L9=Part.makeLine(V9,V10)
    L10=Part.makeLine(V10,V11)
    L11=Part.makeLine(V11,V12)
    L12=Part.makeLine(V12,V1)

    W=Part.Wire([L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12])
    F=Part.Face(W)
    P=F.extrude(FreeCAD.Vector(0,0,z))
    return P
#------------------------------------------------------------------------------
def Draw_Steel_Track(x,y,falange,th1,lcut=0,rcut=0,fliped=0):
    '''Version=2.0
    Draw a Steel Track
    x=Length
    y=Width
    falange=Falange Height
    Th1=steel thickness
    fliped=[boolean] Draw falange to +z?'''
    F=1
    if fliped ==0:
        F=-1
    # Vertices del canal
    V1=FreeCAD.Vector(0,0,0)
    V11=FreeCAD.Vector(0,th1,0)
    V12=FreeCAD.Vector(0,y-th1,0)
    V2=FreeCAD.Vector(0,y,0)
    V3=FreeCAD.Vector(0,y,falange*F)
    V4=FreeCAD.Vector(0,y-th1,falange*F)
    V5=FreeCAD.Vector(0,y-th1,(th1*F))
    V6=FreeCAD.Vector(0,th1,th1*F)
    V7=FreeCAD.Vector(0,th1,falange*F)
    V8=FreeCAD.Vector(0,0,falange*F)


    #Lines
    L1=Part.makeLine(V1,V11) #changed Line to makeLine
    L2=Part.makeLine(V11,V12)
    L3=Part.makeLine(V12,V2)
    L4=Part.makeLine(V2,V3)
    L5=Part.makeLine(V3,V4)
    L6=Part.makeLine(V4,V5)
    L7=Part.makeLine(V5,V6)
    L8=Part.makeLine(V6,V7)
    L9=Part.makeLine(V7,V8)
    L10=Part.makeLine(V8,V1)
    L11=Part.makeLine(V6,V11)
    L12=Part.makeLine(V12,V5)

    W1=Part.Wire([L1,L11,L8,L9,L10])
    W2=Part.Wire([L2,L12,L7,L11])
    W3=Part.Wire([L3,L4,L5,L6,L12])
    F1=Part.Face(W1)
    F2=Part.Face(W2)
    F3=Part.Face(W3)
    S1=F1.extrude(FreeCAD.Vector(x,0,0))
    S2=F2.extrude(FreeCAD.Vector(x-lcut-rcut,0,0))
    S2.Placement.Base=FreeCAD.Vector(lcut,0,0)
    S3=F3.extrude(FreeCAD.Vector(x,0,0))
    P=S1.fuse(S2)
    P=P.fuse(S3)    
    P=P.removeSplitter()

    return P
#------------------------------------------------------------------------------
def Draw_Box_Beam(x,y,y1,z,th1,falange=8,box=1,FEM=True):
    '''Author = Humberto Hassey
    Version=1.0
    Draw a Steel stud
    x=Length
    y=Width of the whole box
    y1=width of the individual stud
    z=height
    Th1=steel thickness'
    '''
    def Draw_half(x,y1,z,th1,falange=8,fliped =0,FEM=True):    
        y=y1
        F=1
        if fliped ==1:
            F=-1
        # Vertices del stud
        V1=FreeCAD.Vector(0,0,0)
        V2=FreeCAD.Vector(0,y*F,0)
        V3=FreeCAD.Vector(0,y*F,falange)
        V4=FreeCAD.Vector(0,(y-th1)*F,falange)
        V5=FreeCAD.Vector(0,(y-th1)*F,th1)
        V6=FreeCAD.Vector(0,th1*F,th1)
        V7=FreeCAD.Vector(0,th1*F,z-th1)#x por z
        V8=FreeCAD.Vector(0,(y-th1)*F,z-th1)
        V9=FreeCAD.Vector(0,(y-th1)*F,z-falange)
        V10=FreeCAD.Vector(0,y*F,z-falange)
        V11=FreeCAD.Vector(0,y*F,z)
        V12=FreeCAD.Vector(0,0,z)

        #Lines
        L1=Part.makeLine(V1,V2)
        L2=Part.makeLine(V2,V3)
        L3=Part.makeLine(V3,V4)
        L4=Part.makeLine(V4,V5)
        L5=Part.makeLine(V5,V6)
        L6=Part.makeLine(V6,V7)
        L7=Part.makeLine(V7,V8)
        L8=Part.makeLine(V8,V9)
        L9=Part.makeLine(V9,V10)
        L10=Part.makeLine(V10,V11)
        L11=Part.makeLine(V11,V12)
        L12=Part.makeLine(V12,V1)
    
        W=Part.Wire([L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12])
        F=Part.Face(W)
        P=F.extrude(FreeCAD.Vector(x,0,0))
        return P
    p1=Draw_half(x,y1,z,th1,falange,0)
    p2=Draw_half(x,y1,z,th1,falange,1)
    if  box==1:
        v1=FreeCAD.Vector(0,-y/2.0+((th1+1.7272)*FEM),0) #1.72=ga14 de la pieza con la que se monta la viga        
        v2=FreeCAD.Vector(0,y/2.0-((th1+1.7272)*FEM),0)
        p1.Placement.Base=v1
        p2.Placement.Base=v2
    P=p1.fuse(p2)
    #comp=Part.makeCompound([p1,p2])
    
    return P# comp
#------------------------------------------------------------------------------
def vigass(vigas):
    '''Funcion que sustituye una lista de vigas=[(pos x,longitud)] y entrega una
    lista mejorada en que los traslapes son contados como una sola viga
    para poner una sola viga sobre ventanas/puertas que se traslapan'''
    def isin(x1,x2,xt1,xt2):
        if (x1<=xt1) and (xt1 <= x2): #se traslapan las trabes y deb en cambiarse por una
            return True
        else:
            return False
    vigas.sort(key=lambda item: item[0])
    for indice,a in enumerate (vigas[:-1]):
        x1_inicial=a[0]
        x1_final=x1_inicial+a[1]
        x2_inicial=vigas[indice+1][0]
        x2_final=x2_inicial+vigas[indice+1][1]
        if isin(x1_inicial,x1_final,x2_inicial,x2_final): #Trabes Traslapadas
            vigas.pop(indice)
            vigas.pop(indice)
            vigas.insert(0,(x1_inicial,max(x2_final,x1_final)-x1_inicial))
            return vigass(vigas) #repeat until there are no overlaping beams
    return vigas
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
class Steel_Frame:
    def __init__ (self , obj):
        self.Object = obj #line not neccesary this was to try to keep the object after copying
        doc=App.ActiveDocument
        obj.Proxy = self
        obj.addProperty("App::PropertyBool","FEM","Frame").FEM=False
        obj.addProperty("App::PropertyStringList","Windows","Frame").Windows=['1200,900,1000,1000']
        obj.addProperty("App::PropertyLength","Length","Frame").Length=3500
        obj.addProperty("App::PropertyLength","Height","Frame").Height=3000
        obj.addProperty("App::PropertyLength","Width","Frame").Width=152.4
        obj.addProperty("App::PropertyLength","Separation","Frame").Separation=304.8
        obj.addProperty("App::PropertyLength","Falange","Stud").Falange=41.275
        obj.addProperty("App::PropertyLength","Lip","Stud").Lip=8
        obj.addProperty("App::PropertyLength","Thickness","Steel").Thickness=0.8382
        obj.addProperty("App::PropertyQuantity","Gauge","Steel").Gauge=22
        obj.addProperty("App::PropertyQuantity","Weight","Take Off").Weight=0
        obj.addProperty("App::PropertyLength","Stud_L","Take Off").Stud_L=0
        obj.addProperty("App::PropertyLength","Track_L","Take Off").Track_L=0
        obj.addProperty("App::PropertyBool","Structural","Structural").Structural=False
        obj.addProperty("App::PropertyLength","Beam_Height","Structural").Beam_Height=150
        obj.addProperty("App::PropertyLength","Stud_Width","Structural").Stud_Width=41.275
        obj.addProperty("App::PropertyBool","Box","Structural").Box=True
    #def onChanged(self, fp, prop):
        #FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")
    #def onChanged(self, obj, prop):
     #   App.activeDocument().recompute()
    def onDocumentRestored(self, obj):
        '''
        Restore object references on reload
        '''
        print ('Document Restored')
        self.Object = obj
    def execute(self,obj):
        ventanas=[]
        trabes=[] #trabes estructurales
        nvent=len(obj.Windows)
        if obj.Windows[0]!='':     # If There are windows in this frame        
            for a in range(len(obj.Windows)):
                ventanas.append(eval(obj.Windows[a])) #crea la lista de ventanas        
                trabes.append((eval(obj.Windows[a])[0],eval(obj.Windows[a])[2]))
        puertas=[x for x in ventanas if x[1]==0] #obtener todas las puertas para poder cortar el track de abajo
        puertas.sort(key=lambda tup: tup[0])        #ordenar las puertas por coordenada x
        ltrack=0 #contadores para cuantificacion de track y stud
        lstud=0 #contadores para cuantificacion de track y stud
        #post_W=0
        FEM=not(obj.FEM)#FEM=hacer postes y tracks mismo tamaño
                
        gauges={25:0.4572, 22:0.6858, 20:0.8382, 18:1.0922, 16:1.3716, 14:1.7272, 12:2.4638,10:2.9972}
        if obj.Gauge.Value in gauges and obj.Gauge.Value !=0:
            obj.Thickness.Value=gauges[obj.Gauge.Value]
        else:
            obj.Gauge.Value=0
        if obj.Thickness.Value  not in gauges.values() and obj.Gauge.Value !=0:
            obj.Gauge.Value=0
        x=obj.Falange.Value; y =obj.Width.Value; z=obj.Height.Value; th1=obj.Thickness.Value
        fal=obj.Lip.Value; Flip=0
        postes=calcStuds(obj.Length.Value,obj.Height.Value,obj.Separation.Value,obj.Falange.Value,ventanas,FEM,0,obj.Structural,obj.Beam_Height.Value,thick=th1)    #0 decia th1
        parte=[] #list of parts that will make the frame
################### Dibuja Postes
        for ip,poste in enumerate(postes):  #-1 para que no dibuje el poste final, pues este va volteado
            parte.append(Draw_Steel_Stud(y-2*th1*FEM,x,th1,poste[2]-2*th1*FEM,fal,poste[3])) #dibujar poste
            parte[ip].Placement.Base=FreeCAD.Vector(poste[0],th1*FEM,poste[1]+th1*FEM)#Colocar poste #corregir Z para FEM
            lstud+=poste[2]-2*th1*FEM
        
################## Dibuja Tracks
        #dibujo track de abajo        
        if len(puertas)==0:    #si no hay puertas el track de abajo va corrido    
            L=obj.Length.Value 
            lt=Draw_Steel_Track(L,y,obj.Falange.Value,th1,fliped=1)
            lt.Placement.Base=FreeCAD.Vector(0,0,0)
            ltrack+=L
            parte.append(lt)
        else:
            #dibuja el track desde 0 a la primer puerta
            L=puertas[0][0]
            lt=Draw_Steel_Track(L,y,obj.Falange.Value,th1,fliped=1)
            lt.Placement.Base=FreeCAD.Vector(0,0,0)
            ltrack+=L
            parte.append(lt)
            #dibuja el track desde la puerta n a la n+1
            Puertas_hechas=1
            while len(puertas)>Puertas_hechas:
                L=puertas[Puertas_hechas][0]-puertas[Puertas_hechas-1][0]-puertas[Puertas_hechas-1][2]
                lt=Draw_Steel_Track(L,y,obj.Falange.Value,th1,fliped=1)
                pos=puertas[Puertas_hechas-1][0]+puertas[Puertas_hechas-1][2] #calculo de la posicion del tramo
                lt.Placement.Base=FreeCAD.Vector(pos,0,0)
                ltrack+=L
                parte.append(lt)
                Puertas_hechas+=1
            #dibujar tramo de la ultima puerta al final
            L=obj.Length.Value-(puertas[-1][0]+puertas[-1][2])
            lt=Draw_Steel_Track(L,y,obj.Falange.Value,th1,fliped=1)
            lt.Placement.Base=FreeCAD.Vector(puertas[-1][0]+puertas[-1][2],0,0)
            ltrack+=L
            parte.append(lt)
##########Dibujo del Track de arriba
        L=obj.Length.Value         
        tt=Draw_Steel_Track(L,y,obj.Falange.Value,th1,fliped=0) #top Track
        tt.Placement.Base=FreeCAD.Vector(0,0,z)
        ltrack+=L
        parte.append(tt)
        for vent in ventanas: #dibujo Tracks de ventanas y puertas
            v=Draw_Steel_Track(vent[2]+2*x,y,x,th1,x,x,1) #top piece x=flange
            v.Placement.Base=FreeCAD.Vector(vent[0]-x,0,vent[1]+vent[3])
            ltrack+=vent[2]+2*x
            parte.append(v)
            if vent[1]!=0:     #si es puerta no dibujo track abajo        
                v1=Draw_Steel_Track(vent[2]+2*x,y,x,th1,x,x,0) #bottom piece x=flange
                v1.Placement.Base=FreeCAD.Vector(vent[0]-x,0,vent[1])
                ltrack+=vent[2]+2*x
                parte.append(v1)
################## Dibujo Trabes Estructurales Box Beams
        if obj.Structural ==True:
            trabes=vigass(trabes)
            for a in trabes:
                xs=a[1] #longitud de la trabe
                ys=obj.Stud_Width.Value
                yf=obj.Width.Value
                zs=obj.Beam_Height.Value            
                sb1=Draw_Box_Beam(xs,yf,ys,zs,th1,obj.Lip.Value,obj.Box,FEM)
                sb1.Placement.Base=FreeCAD.Vector(a[0],y/2,obj.Height.Value-obj.Beam_Height.Value-(th1*FEM))
                parte.append(sb1)
                #Draw Track Below beam...
                sb2=Draw_Steel_Track(xs,obj.Width.Value,obj.Falange.Value,th1,lcut=0,rcut=0,fliped=0)
                sb2.Placement.Base=FreeCAD.Vector(a[0],0,obj.Height.Value-obj.Beam_Height.Value-(th1*FEM))
                ltrack+=xs
                parte.append(sb2)
                #aqui Falta Agregar las longitudes de las secciones OJO OJO OJO OJO OJO
                
            #####dibujo de piezas especiales para el montaje de la trabe
                if obj.Box:
                    e1=Draw_Steel_Track(zs,yf-(2*th1*FEM),obj.Falange.Value,1.7272,lcut=0,rcut=0,fliped=0)#Ga14
                    e1.Placement.Rotation= App.Rotation(App.Vector(0,1,0),-90)
                    e1.Placement.Base=FreeCAD.Vector(a[0],th1*FEM,obj.Height.Value-obj.Beam_Height.Value-(th1*FEM))
                    e2=Draw_Steel_Track(zs,yf-(2*th1*FEM),obj.Falange.Value,1.7272,lcut=0,rcut=0,fliped=1)
                    e2.Placement.Rotation= App.Rotation(App.Vector(0,1,0),-90)
                    e2.Placement.Base=FreeCAD.Vector(a[0]+a[1],th1*FEM,obj.Height.Value-obj.Beam_Height.Value-(th1*FEM))
                    parte.append(e1)
                    parte.append(e2)
        comp=Part.makeCompound(parte)
        if obj.FEM: #make one solid for FEM analysis
            comp=Part.makeSolid(comp) 
            comp2=comp.removeSplitter()
            obj.Shape=comp2
            print('Center of Mass',obj.Shape.CenterOfMass)
        obj.Shape=comp
        obj.Weight=comp.Volume*7850/1e9
        obj.Stud_L=FreeCAD.Units.Metre*lstud/1e3
        obj.Track_L=FreeCAD.Units.Metre*ltrack/1e3
    
########## Calculo centro de masa
        if not(obj.FEM):    
            v=FreeCAD.Vector(0,0,0)
            solidos=obj.Shape.Solids 
            for b in solidos:
                v2=b.CenterOfMass*b.Volume
                v=v.add(v2)
            vt=obj.Shape.Volume
            print('Center of Mass',v*(1/vt))
            
#a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Steel_Frame")
#Steel_Frame(a)
#a.ViewObject.Proxy    =    0

#App.ActiveDocument.recompute()
