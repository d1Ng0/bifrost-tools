# !/usr/bin/env mayapy

"""
This script can be used to generate wedges of Bifrost simulations.
By parsing a scene file and a set of attributes can simulate, render and combine a video with an overlay of the adributes used.
The script will also save out a copy of the maya file into the cache directory so it won't overwrite current files and the Artists will be able to open up the source fileused to generate the simulations.  

Keyword arguments: 
mayaFile          -- Maya file to use for simulation wedge.                                                  --  REQUIRED -- 
projDir           -- Project path. This is used for setting up cache and render directories.                 --  REQUIRED -- 
contrainerName    -- Name of the Bifrost container in the scene which will be used for the simulation wedge. --  REQUIRED -- 
node              -- Node to use for wedge followed by attribute name. Example: --node emitterShape.bifrostLiquidStictionStrength --  REQUIRED -- 
wedge             -- A list containing the values of attribues to wedge over. Example: --wedge 0 2 4         --  REQUIRED -- 
frames            -- Start and end frame for the simulation. Example --frames 1 100                          --  REQUIRED -- 
dryRun            -- If active will only generate Maya scene files withouth running the simulation. Used for debugging purposes.
montage           -- If active will tile images after rendering and add watermarks to the final compositing

Example : 
./biFrostWedge.py --mayaFile ~/GDrive/VFX/CMI/CrashingWaveShading/scenes --projDir ~/GDrive/VFX/CMI/CrashingWaveShading --containerName bifrostLiquidContainer1 --node bifrostLiquidContainer1.vorticityMult --wedge 0 1 2 3 5 8 --frames 1 600 --montage

Ignore this:
ffmpeg -y -f image2 -r 24 -i Montage.%04d.jpg -vcodec h264 -s 1280x720 stictionStrength.mov
For full logging set: 
setenv BIFROST_DUMP_STATE_SERVER 0
ImageMagik for Mac Maverics can be downloaded here: http://cactuslab.com/imagemagick/
"""

import sys
import os
import argparse
import subprocess
import maya.cmds as cmds
import maya.standalone

class biFrostWedge():

    def __init__(self):

        parser = argparse.ArgumentParser(description='BiFrost wedge tool.', epilog='For support or feedback email Diego Trazzi')
        parser.add_argument('--mayaFile', '-f', required=True, help='Maya scene file name')
        parser.add_argument('--projDir', required=True, help='Maya project directory')
        parser.add_argument('--containerName', required=True, help='Name of the Bifrost container: eg,: bifrostLiquidContainer1')
        parser.add_argument('--node', required=True, help='Node to wedge followed by attribute name. Example: emitterShape.bifrostLiquidStictionStrength')
        parser.add_argument('--wedge', required=True, nargs='+', help='Wedge list. Example : 0 2 4')
        parser.add_argument('--frames', required=True, type=int, help='Define the frame range. Required to run', nargs=2)
        parser.add_argument('--dryRun', help='Optional flag for generating maya files only ( Default = False )', action='store_true', default=False)
        parser.add_argument('--montage', help='Generate tiled images from cached wedge of simulations. Do this as post process after the simulations are finished ( Default = False )', action='store_true', default=False)

        # PARSE ARGUMENTS FROM COMMAND LINE
        args = parser.parse_args()

        # JUMP TO MAIN 
        self.main(mayaFile=args.mayaFile, projDir=args.projDir, containerName=args.containerName, wedgeNode=args.node, wedgeList=args.wedge, dryRun=args.dryRun, montage=args.montage, frames=args.frames)

    def main(self, mayaFile, projDir, containerName, wedgeNode, wedgeList, dryRun, montage, frames):

        sceneName = os.path.split(mayaFile)[-1].split('.')[0]
        cacheDir = os.path.join(projDir, 'cache', 'bifrost', sceneName, wedgeNode.replace('.', '_'))
        if not os.path.exists(cacheDir):
            os.makedirs(cacheDir)
        print(
            "Maya file to wedge:" + '\t' * 3 + mayaFile + '\n' + 
            "Maya project directory:" + '\t' * 3 + projDir + '\n' + 
            "Node and attribute to wedge:" + '\t' * 2 + wedgeNode + '\n' + 
            "Wedge list:" + '\t' * 4 + str(wedgeList) + '\n'
            )

        # LOOP THROUGHT THE WEDGE LIST
        for i in range(len(wedgeList)):
            print('\nWedge numer:\t%02d' % i)
            # GENERATE A NEW MAYA WEDGE FILE
            wedgeName = wedgeNode.replace('.', '_') + '_%02d' % (i)
            try: 
                wedgePath = self.wedgeSetup(mayaFile, cacheDir, containerName, wedgeName, wedgeNode, wedgeList[i])
            except: 
                print(sys.exc_info())
                sys.exit("Couldn't setup wedgescene file")

            if not dryRun:
                # RUN A RENDER SESSION WITH THE WEDGE FILE
                subprocess_cmd = 'Render -renderer hw2 -fnc 3 -s {0} -e {1} -pad 4 -x 1280 -y 720 -of jpg -proj {2} -rd {3} -im {4} {5}'.format(frames[0], frames[1], projDir, cacheDir, wedgeName, wedgePath)
                # We use subprocess.call because we don't want to fork a separate process
                # (which is what Popen does). Don't specify stdout because for some reason
                # it's bein suppressed.
                subprocess.call(subprocess_cmd, stderr=subprocess.STDOUT, shell=True)
            else:
                sys.exit("Not running render. Option dryRun set True")
                print(subprocess_cmd)
        # MONTAGE
        if montage:
            self.montage(cacheDir, wedgeNode, wedgeList, frames)
        return


    def wedgeSetup(self, mayaFile, cacheDir, containerName, wedgeName, wedgeNode, wedgeAttr):        
        try:
            attr = float(wedgeAttr)
        except ValueError:
            print(sys.exc_info())
            sys.exit("Cant convert {0} into a float number".format(wedgeAttr))
        try:
            # Initialize a new instance of maya
            maya.standalone.initialize()
            # Open up the source maya scene file
            self.loadMaya()
            cmds.file(mayaFile, open=True)
        except: 
            print(sys.exc_info())
            sys.exit("Something went wrong while trying to open the maya scene file: {0}. Check the path and try again".format(mayaFile))
        
        # Select node for wedge and change attrs
        try: 
            print(wedgeNode)
            print(attr)
            cmds.setAttr(wedgeNode, attr)
        except:
            print(sys.exc_info())
            sys.exit("Couldn't set the wedge attributes {0} on this node: {1}".format(attr, wedgeNode))
        # Set containerNode to write cache
        try:
            # Wrties cache on /tmp folder
            # cmds.setAttr(containerName+'.cachingControl', 0)
            # Writes cache on cache folder
            cmds.setAttr(containerName + '.enableDiskCache', 1)
            cmds.setAttr(containerName + '.cachingControl', 2)
            # This will break window version --> adding /
            cmds.setAttr(containerName + '.cacheDir', cacheDir + '/', type="string")
            cmds.setAttr(containerName + '.cacheName', wedgeName, type="string")
        except: 
            print(sys.exc_info())        
            sys.exit("Couldn't set the Bifrost container: {0} to write status".format(containerName))
        # Rename the scene file and saves it
        try:
            # Setup new file name
            wedgePath = os.path.join(cacheDir, wedgeName + '.mb')
            print(wedgePath)
            # save new maya scene file
            cmds.file(rename=wedgePath)
            cmds.file(save=True, force=True, defaultExtensions=False, type='mayaBinary')
        except:
            print(sys.exc_info())
            sys.exit("Can't save to the following location: {0}. Please check and try agian".format(wedgePath))
        # QUIT MAYA
        cmds.quit(force=True)
        print("Success")
        return wedgePath


    def loadMaya(self):
        maya.standalone.initialize()


    def montage(self, cacheDir, wedgeNode, wedgeList, frames, fps=23.98):
        # ADD TEXT TO THE RENDER FRAMES
        for f in range(frames[0], frames[1] + 1):
            tileImages = []
            frame = '{0:04d}'.format(f)
            try:
                for i in range(len(wedgeList)):                
                    wedgeName = wedgeNode.replace('.', '_') + '_%02d' % (i)
                    wedgeText = '{0}: {1}'.format(wedgeName, wedgeList[i])
                    imageFile = os.path.join(cacheDir, (wedgeName + '.' + frame + '.jpg'))
                    tileImages.append(imageFile)
                    subprocess_text_cmd = 'convert {0} -font Arial -pointsize 40 -background Khaki label:\'{1}\' -gravity Center -append {0}'.format(imageFile, wedgeText)
                    print(subprocess_text_cmd)
                    subprocess.call(subprocess_text_cmd, stderr=subprocess.STDOUT, shell=True)
            except:
                sys.exc_info()
                sys.exit("Something wrong happened while adding text to the rendered images. Please check you have imageMagik installed properly")
    
            # TILE IMAGES TOGETHER
            try: 
                images = ' '.join(tileImages)
                wedgePath = os.path.join(cacheDir, ('Montage.' + frame + '.jpg'))
                subprocess_tile_cmd = 'montage -geometry +0+0 {0} {1}'.format(images, wedgePath)
                print(subprocess_tile_cmd)
                subprocess.call(subprocess_tile_cmd, stderr=subprocess.STDOUT, shell=True)
                # RESIZE IMAGES TO HD FORMAT
                subprocess_resize_cmd = 'convert -resize 1280x720 {0} {1}'.format(wedgePath, wedgePath)
                print(subprocess_resize_cmd)
                subprocess.call(subprocess_resize_cmd, stderr=subprocess.STDOUT, shell=True)
            except: 
                sys.exit("Something wrong happened while tiling images together")

        # MAKE A QUICKTIME
        try:
            movPath = os.path.join(cacheDir, 'Montage.mov')
            subprocess_mkMovie_cmd = 'ffmpeg -r {0} -i {1} -c:v libx264 -s 1280x720 {2}'.format(fps, os.path.join(cacheDir, 'Montage.%04d.jpg'), movPath)
            print(subprocess_mkMovie_cmd)
            subprocess.call(subprocess_mkMovie_cmd, stderr=subprocess.STDOUT, shell=True)
            print("Successfully generated wedge. Quicktime file: {0}".format(movPath))
            return movPath
        except:
            print("Something wrong happened while generating the quicktime movie")
            print(sys.exc_info())
            return


if __name__ == "__main__":
    app = biFrostWedge()
