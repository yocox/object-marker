#!/usr/bin/python
 
###############################################################################
# Name      : ObjectMarker.py
# Author    : Python implementation: sqshemet 
#         Original ObjectMarker.cpp: http://www.cs.utah.edu/~turcsans/DUC_files/HaarTraining/
# Date      : 7/24/12
# Description   : Object marker utility to be used with OpenCV Haar training. 
#         Tested on Ubuntu Linux 10.04 with OpenCV 2.1.0.
# Usage     : python ObjectMarker.py outputfile inputdirectory
###############################################################################
 
import cv
import sys
import os
import glob
 
IMG_SIZE = (300,300)
IMG_CHAN = 3
IMG_DEPTH = cv.IPL_DEPTH_8U
current_image = cv.CreateImage(IMG_SIZE, IMG_DEPTH, IMG_CHAN)
image2 = cv.CreateImage(IMG_SIZE, IMG_DEPTH, IMG_CHAN) 
has_roi = False
roi_x0 = 0
roi_y0 = 0
roi_x1 = 0
roi_y1 = 0
cur_mouse_x = 0
cur_mouse_y = 0
num_of_rec = 0
draging = False
window_name = "<Space> to save and load next, <X> to skip, <ESC> to exit."
current_img_file_name = ""

table_file_name = ''
background_file_name = ''
image_file_glob = ''
 
rect_table = {}
background_files = set()

def read_rect_table() :
    if os.path.exists(table_file_name) :
        fin = open(table_file_name)
        lines = fin.readlines()
        cnt_all_rects = 0
        for line in lines :
            tokens = line.split()
            pic_name = tokens[0]
            rect_table[pic_name] = set()
            num_rect = int(tokens[1])
            cnt_all_rects += num_rect
            for i in range(0, num_rect) :
                rect = tuple(tokens[i * 4 + 2 : i * 4 + 6])
                rect = tuple([int(v) for v in rect])
                rect_table[pic_name].add(rect)
        print 'Reading %d objects in %d images' % (cnt_all_rects, len(lines))

    if os.path.exists(background_file_name) :
        fin = open(background_file_name)
        lines = fin.readlines()
        for line in lines :
            background_files.add(line.strip())

def write_rect_table() :
    fout = open(table_file_name, 'w')
    for (f, rect_set) in rect_table.iteritems() :
        if len(rect_set) == 0 :
            continue
        fout.write(f + '  ' + str(len(rect_set)))
        for r in rect_set :
            rect_str = '  %d %d %d %d' % r
            fout.write(rect_str)
        fout.write('\n')

    fout = open(background_file_name, 'w')
    for f in background_files :
        fout.write(f + '\n')

def clear_roi() :
    global has_roi
    global roi_x0
    global roi_y0
    global roi_x1
    global roi_y1

    has_roi = False
    roi_x0 = 0
    roi_y0 = 0
    roi_x1 = 0
    roi_y1 = 0

def redraw() :
    global draging
    global has_roi
    global roi_x0
    global roi_y0
    global cur_mouse_x
    global cur_mouse_y
    #Redraw ROI selection
    image2 = cv.CloneImage(current_image)

    # redraw old rect
    pen_width = 4
    if rect_table.has_key(current_img_file_name) :
        rects_in_table = rect_table[current_img_file_name]
        for r in rects_in_table :
            cv.Rectangle(image2, (r[0], r[1]), (r[0] + r[2], r[1] + r[3]), cv.CV_RGB(0,255,0),pen_width)

    # redraw new rect
    if has_roi :
        cv.Rectangle(image2, (roi_x0, roi_y0), (cur_mouse_x, cur_mouse_y), cv.CV_RGB(255,0,255),pen_width)

    # draw background
    if current_img_file_name in background_files :
        cv.Line(image2, (0, 0), (image2.width, image2.height), cv.CV_RGB(255, 0, 0))
        cv.Line(image2, (0, image2.height), (image2.width, 0), cv.CV_RGB(255, 0, 0))

    cv.ShowImage(window_name, image2)

def remove_rect(x, y):
    if not rect_table.has_key(current_img_file_name) :
        return

    rects_contain_xy = set()
    rects_in_table = rect_table[current_img_file_name]
    for r in rects_in_table :
        if x < r[0] : continue
        if y < r[1] : continue
        if x > r[0] + r[2] : continue
        if y > r[1] + r[3] : continue
        rects_contain_xy.add(r)

    for r in rects_contain_xy :
        rects_in_table.remove(r)

    rect_table[current_img_file_name] = rects_in_table
    if len(rects_contain_xy) > 0 :
        redraw()

    write_rect_table()

def on_mouse(event, x, y, flag, params):
    global current_img_file_name
    global draging
    global has_roi
    global roi_x0
    global roi_y0
    global roi_x1
    global roi_y1
    global cur_mouse_x
    global cur_mouse_y

    cur_mouse_x = x
    cur_mouse_y = y

    if (event == cv.CV_EVENT_LBUTTONDOWN):
        draging = True
        has_roi = True
        roi_x0 = x
        roi_y0 = y
    elif (event == cv.CV_EVENT_LBUTTONUP):
        draging = False
        has_roi = True
        roi_x1 = x
        roi_y1 = y

        # normalize
        if roi_x1 < roi_x0 :
            roi_x0, roi_x1 = roi_x1, roi_x0 
        if roi_y1 < roi_y0 :
            roi_y0, roi_y1 = roi_y1, roi_y0 

    elif (event == cv.CV_EVENT_RBUTTONDOWN):
        clear_roi()
        redraw()

    elif (event == cv.CV_EVENT_MOUSEMOVE):
        if draging:
            redraw()
 
def main():
 
    global current_image
    global current_img_file_name
    global has_roi
    global roi_x0
    global roi_y0
    global roi_x1
    global roi_y1

    iKey = 0
    
    files = glob.glob(image_file_glob)
    if len(files) == 0 :
        print "No files match glob pattern"
        return
 
    files = [os.path.abspath(f) for f in files]
    files.sort()
 
    # init GUI
    cv.NamedWindow(window_name, 1)
    cv.SetMouseCallback(window_name, on_mouse, None)
 
    sys.stderr.write("Opening directory...")
    # init output of rectangles to the info file
    #os.chdir(input_directory)
    sys.stderr.write("done.\n")
 
    current_file_index = 0
 
    while True :

        current_img_file_name = files[current_file_index]

        num_of_rec = 0
        sys.stderr.write("Loading current_image (%d/%d) %s...\n" % (current_file_index + 1, len(files), current_img_file_name))
 
        try: 
            current_image = cv.LoadImage(current_img_file_name, 1)
        except IOError: 
            sys.stderr.write("Failed to load current_image %s.\n" % current_img_file_name)
            return -1
 
        #  Work on current current_image
        #cv.ShowImage(window_name, current_image)
        redraw()

        # Need to figure out waitkey returns.
        # <Space> =  32     add rectangle to current image
        # <left>  =  81     save & next
        # <right> =  83     save & prev
        # <a>     =  97     add rect to table
        # <b>     =  98     toggle file is background or not
        # <d>     = 100     remove old rect
        # <q>     = 113     exit program
        # <s>     = 115     save rect table
        # <x>     = 136     skip image
        iKey = cv.WaitKey(0) % 255
        # This is ugly, but is actually a simplification of the C++.
        #sys.stderr.write(str(iKey) + '\n')
        if draging :
            continue

        if iKey == 81:
            current_file_index -= 1
            if current_file_index == -1 :
                current_file_index = len(files) - 1
            clear_roi()
        elif iKey == 83:
            current_file_index += 1
            if current_file_index == len(files) :
                current_file_index = 0
            clear_roi()
        elif iKey == 113:
            cv.DestroyWindow(window_name)
            return 0
        elif iKey == 97:
            rect_table.setdefault(current_img_file_name, set()).add((roi_x0, roi_y0, roi_x1 - roi_x0, roi_y1 - roi_y0)) 
            clear_roi()
            write_rect_table()
            redraw()
        elif iKey == 98:
            if current_img_file_name in background_files :
                background_files.remove(current_img_file_name)
            else :
                background_files.add(current_img_file_name)
        elif iKey == 100:
            remove_rect(cur_mouse_x, cur_mouse_y)
        elif iKey == 115:
            write_rect_table()
        elif iKey == 136:
            sys.stderr.write("Skipped %s.\n" % current_file_index)
        
if __name__ == '__main__':
    print sys.argv
    if (len(sys.argv) != 4):
        sys.stderr.write("usage: %s objects.txt background.txt 'image_glob_pattern'\n" % sys.argv[0])
        sys.stderr.write("example: %s objects.txt background.txt 'training_img/*.png'\n" % sys.argv[0])
    else:
        table_file_name      = sys.argv[1]
        background_file_name = sys.argv[2]
        image_file_glob      = sys.argv[3]

        read_rect_table()
        main()

