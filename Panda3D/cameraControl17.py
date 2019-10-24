# control window position and size
from pandac.PandaModules import loadPrcFileData

loadPrcFileData("", "win-size 3120 780")
loadPrcFileData("", "win-origin 1920 100")
# loadPrcFileData("", "win-size 1040 260")
# loadPrcFileData("", "win-origin 10 0")


from direct.showbase.DirectObject import DirectObject  # KH: provides .accept
from pandac.PandaModules import CollisionHandlerFloor, CollisionHandlerPusher, CollisionNode, CollisionSphere, \
    CollisionTraverser, BitMask32, CollisionRay, NodePath
import direct.directbase.DirectStart
from direct.task import Task
import scipy.io
import numpy
import win32com.client  # Python ActiveX Client

ha = 0
F = 0
X = 0
z1before = 0
z2before = 0


class MyApp(DirectObject):
    def __init__(self):

        # Load the environment model.
        environ = loader.loadModel("zebrafishEnviron17_100contrast")
        environ.reparentTo(render)
        environ.setScale(1, 1, 1)
        environ.setPos(0, 0, 0)

        # Load AVI texture
        self.tex1 = loader.loadTexture("VRE_autoPA_bigFish.avi")
        self.tex2 = loader.loadTexture("VRE_autoPA_hE.avi")
        self.tex3 = loader.loadTexture("VRE_autoPA_vE.avi")
        self.tex4 = loader.loadTexture("VRE_autoPA_bigFeeding.avi")
        self.texBG = loader.loadTexture("VRE_autoPA_realFishBG.jpg")
        self.texBG4 = loader.loadTexture("VRE_autoPA_feedingBG.jpg")

        self.sound1 = loader.loadSfx("VRE_autoPA_realFish.avi")
        self.sound2 = loader.loadSfx("VRE_autoPA_hE.avi")
        self.sound3 = loader.loadSfx("VRE_autoPA_vE.avi")
        self.sound4 = loader.loadSfx("VRE_autoPA_feeding.avi")

        self.tex1.synchronizeTo(self.sound1)
        self.tex2.synchronizeTo(self.sound2)
        self.tex3.synchronizeTo(self.sound3)
        self.tex4.synchronizeTo(self.sound4)


        # Load TV model and apply baseline texture
        self.TV1 = loader.loadModel("zebrafishEnviron4TV3")
        self.TV2 = loader.loadModel("zebrafishEnviron4TV3")
        self.TV1.reparentTo(render)
        self.TV2.reparentTo(render)
        self.TV1.setTexture(self.tex1, 1)
        self.TV2.setTexture(self.tex1, 1)
        self.TV1.setPos(0, -20.3, 0)
        self.TV2.setPos(0, 20.3, 0)
        self.TV2.setH(180)

        # Add the spinCameraTask procedure to the task manager.
        taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        # KH: taskMgr is an attribute of class ShowBase. It keeps a list of currently-running taks. ".add()" is a method of taskMgr.
        # self.spinCameraTask is a function defined below. "SpinCameraTask" can be an arbitrary name.

        base.disableMouse()
        base.camera.setPos(0, 0, 5)
        base.camLens.setFov(
            40)  # Necessary to set bot horizontal and vertical FOV. If only set horizontal, vertical FOV will be calculated using the aspect ratio of the window.
        base.setAspectRatio(1.33)  # Override window's aspect ratio, which is 3X wider, as specified in the beginning

        # Turn off the default camera and replace it with 3 cameras, with side-by-side displayRegions.
        base.camNode.setActive(0)
        base.makeCamera(base.win, displayRegion=(0.33, 0.66, 0, 1), lens=base.camLens)  # central camera
        base.makeCamera(base.win, displayRegion=(0, 0.33, 0, 1), lens=base.camLens)  # left camera
        base.makeCamera(base.win, displayRegion=(0.66, 0.99, 0, 1), lens=base.camLens)  # right camera

        base.camList[1].setH(0)
        base.camList[2].setH(40)
        base.camList[3].setH(-40)

        # Set collision rules
        base.cTrav = CollisionTraverser()
        environ_mask = BitMask32.bit(2)

        camera.setCollideMask(
            BitMask32.allOff())  # KH: visible geometry nodes also have an "into" mask. Collision should not act on these nodes. Turn the mask off.
        cameraCN = CollisionNode('eye')  # KH: collision node
        cameraCN.addSolid(CollisionSphere(0, 0, 0, 1))
        cameraCN.setFromCollideMask(environ_mask)
        cameraCN.setIntoCollideMask(BitMask32.allOff())
        cameraCNP = camera.attachNewNode(cameraCN)  # KH: collision node path

        environ.setCollideMask(BitMask32.allOff())
        environ.setScale(1)
        wallCNP = environ.find("**/wall_collide")  # KH: CNP for environ, you manually set the <Collide> tag in egg file
        wallCNP.node().setIntoCollideMask(environ_mask)
        eHandler = CollisionHandlerPusher()
        eHandler.addCollider(cameraCNP, camera)
        base.cTrav.addCollider(cameraCNP, eHandler)

        # communicate with LabView using ActiveX
        LabVIEW = win32com.client.Dispatch("Labview.Application")
        self.VI = LabVIEW.getvireference('C:\\Friedrich KH\\LabviewPython_reset.vi')  # Path to LabVIEW VI
        self.VI._FlagAsMethod("Call")  # Flag "Call" as Method

    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        global ha
        global F
        global z1before
        global z2before

        # receive info from LabView: yaw & forward
        reset = self.VI.getcontrolvalue('reset_')
        frdOmr = self.VI.getcontrolvalue('frdOmr_')
        yaw = self.VI.getcontrolvalue('yaw_')
        forward = self.VI.getcontrolvalue('forward_')

        if reset is True:
            base.camera.setH(0)
            base.camera.setPos(0, 0, 5)
        else:
            if frdOmr is True:
                ha = 0
                F = (F + forward) % 60
                X = 40
            else:
                ha = ha + yaw
                F = (F + forward)
                X = 0
        base.camera.setH(
            ha)  # KH: globalClock is in class DirectStart. getDt() gets the time (in seconds) since the last frame was drawn:
        base.camera.setY(base.camera, forward)

        # send info to LabView: x, y, heading direction
        checkPos = base.camera.getPos()
        x = checkPos[0]
        y = checkPos[1]
        HA = base.camera.getH()
        vreFps = round(globalClock.getDt() * 1000)
        self.VI.setcontrolvalue('x_', str(x))
        self.VI.setcontrolvalue('y_', str(y))
        self.VI.setcontrolvalue('HA_', str(HA))
        self.VI.setcontrolvalue('vreFps', str(vreFps))


        # receive info from LabView: movieID
        z1 = self.VI.getcontrolvalue('movie R')
        z2 = self.VI.getcontrolvalue('movie L')

        if z1 - z1before != 0:
            if z1 == 1:
                self.TV2.setTexture(self.tex1, 1)
                self.TV1.setTexture(self.texBG, 1)
            elif z1 == 2:
                self.TV2.setTexture(self.tex2, 1)
                self.TV1.setTexture(self.texBG, 1)
            elif z1 == 3:
                self.TV2.setTexture(self.tex3, 1)
                self.TV1.setTexture(self.texBG, 1)
            elif z1 == 4:
                self.TV2.setTexture(self.tex4, 1)
                self.TV1.setTexture(self.texBG4, 1)

        if z2 - z2before == 1:
            self.sound1.play()
        elif z2 - z2before == 2:
            self.sound2.play()
        elif z2 - z2before == 3:
            self.sound3.play()
        elif z2 - z2before == 4:
            self.sound4.play()

        z1before = z1
        z2before = z2
        # KH setHpr(yaw, pitch, row): default angle points to y axis (i.e. away from you, into the monitor)
        # Positive yaw = left, Positive pitch = up, Positive row = clockwise if look along y axis.
        return Task.cont  # KH: the output of a task is either Task.cont  or Task.done


app = MyApp()
run()
