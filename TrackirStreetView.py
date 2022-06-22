#!/usr/bin/env python3
#TrackIR Websocket Server
#Sergio Trujillo 2022
#sergiotrujillo@gmail.com
#You need to run Trackir software before Python script
#You need TrackClip for head tracking, not tested with TrackClipPro

import asyncio
import threading
import queue
import json
import websockets
from trackir import TrackIRDLL, TrackIR_6DOF_Data, logprint
import time
import signal
import sys
import tkinter
from tkinter import StringVar
import struct
import sys

################################################################################################################

HOST = 'localhost'
PORT = 5000
global window

################################################################################################################

####################

#Start
'''
def btnStartClick():    
    None
    #self.lblYaw.configure(text="btnStartClick !!")
    #tkinter.messagebox.showinfo('Message title', 'Message content')
    #tkinter.messagebox.showwarning('Message title', 'Message content')
    #tkinter.messagebox.showerror('Message title', 'Message content')
'''   
#Stop
'''
def btnStopClick():
    None
    #lblYaw.configure(text="btnStopClick !!")
'''

################################################################################################################
# Ventana
################################################################################################################

def main(window):

    #window = tkinter.Tk()
    #window.title("TrackIR Websocket Server") #Name    
    #window.geometry("500x300") #Size
    #window.iconbitmap("trackir_websockets_server_icon_16.png") #Icon
    #window.config(bg="blue") #Back
    #window.resizable(0,0)

    #Buttons
    '''
    btnStart = tkinter.Button(window, text="Start", command=btnStartClick)
    btnStart.pack(side=BOTTOM, padx=20, pady=20)
    btnStart.grid(column=100, row=500)
    btnStop = tkinter.Button(window, text="Stop", command=btnStopClick)
    btnStop.pack(side=BOTTOM, padx=20, pady=20)
    btnStop.grid(column=200, row=500)
    '''

    #Labels
    '''
    lblYawValueText = StringVar()
    lblYawValueText.set('0')
    lblYawValue = tkinter.Label(window, textvariable=lblYawValueText, font=("Arial Bold", 20)) #tkinter.Entry(window, width=10, state='disabled')
    lblYawValue.grid(column=50, row=0)
    '''
    
    #window.update_idletasks()
    #window.update()
    
################################################################################################################
# TrackirThread
################################################################################################################

class TrackirThread(threading.Thread):

    # overide self init
    def __init__(self,name):
        threading.Thread.__init__(self)
        self.name=name
        self.USERS = set()
        print("Start TrackirThread thread", self.name)

    # overide
    def run(self):

        global data
        
        #app.lblYawValueText.set('3') #antes del mainloop()
        #window.mainloop()

        # We have to create a Window for TrackIR, but we do not need to actually
        # show it, nor run the tkinter event loop.  We set the title though just
        # in case it shows up the Windows Task Manager etc.

        #app = tkinter.Tk()
        #app.title("TrackIR Log to CSV")

        try:
            trackrIr = TrackIRDLL(window.wm_frame())
        except Exception as e:
            #logprint("Crash!\n  (This usually means you need to restart the trackir gui)\n")
            raise e

        previous_frame = -1
        #print("timestamp, framenum, roll, pitch, yaw, x, y, z")
        #logprint("timestamp, framenum, roll, pitch, yaw, x, y, z")
        num_logged_frames = 0
        num_missed_frames = 0
        start_time = time.time()

        def signal_handler(sig, frame):
            trackrIr.stop()
            #logprint("num_logged_frames:", num_logged_frames)
            #logprint("num_missed_frames:", num_missed_frames)
            end_time = time.time()
            #logprint("Total time:", round(end_time - start_time), "s")
            #logprint("Rate:", round(num_logged_frames / (end_time - start_time)), "hz")
            sys.exit(0)
        
        #def signaling():
        #signal.signal(signal.SIGINT, signal_handler)
        #TrackirThread.initialize()

        #signal.signal(signal.SIGINT, signal_handler)        
        #esto que falla he visto alguna solucion:
        if threading.current_thread() is threading.main_thread():
            #logprint ("main_thread", threading.main_thread().name)
            #logprint ("current_thread: ", threading.current_thread().name)
            signal.signal(signal.SIGINT, signal_handler)
        
        while(True): #despues de signal.signal
        
            data = trackrIr.NP_GetData()
            
            if data.frame != previous_frame:
                num_logged_frames += 1
                if previous_frame != -1:
                    num_missed_frames += data.frame - previous_frame - 1
                previous_frame = data.frame
                time_ms = round((time.time() - start_time)*1000)
                #print(time_ms, ',', data.frame, ',', round(data.roll, 1), ',', round(data.pitch, 1), ',', round(data.yaw, 1), ',', round(data.x, 1), ',', round(data.y, 1), ',', round(data.z, 1))            
                #logprint(round(data.yaw, 1))
                #window.lblYawValueText.set(round(data.yaw, 1))
                #Sergio
                #start_server.websocket.send(round(data.yaw, 1))              
                
            time.sleep(1/240) # Sample at ~240hz, for the ~120hz signal
  
################################################################################################################
# WebSocketThread
################################################################################################################

class WebSocketThread (threading.Thread):
    
    # overide self init
    def __init__(self,name):
        threading.Thread.__init__(self)
        self.name=name
        self.USERS = set()
        print("Start WebSocketThread thread", self.name)

    # overide
    def run(self):

        # must set a new loop for asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        # setup a server
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.echo, HOST, PORT))
        # keep thread running
        asyncio.get_event_loop().run_forever()

    #async
    async def echo(self, websocket, path):
            
        while(True):

            message = json.dumps({
                'yaw': round(data.yaw,1),
                'pitch': round(data.pitch,1), 
                'roll': round(data.roll,1)
                })        
           
            try:
                #await
                logprint(message)
                await websocket.send(message)
                #await asyncio.sleep(1)
            except websockets.exceptions.ConnectionClosed:
                print("close: ", websocket)
                break

            #asyncio.sleep(1/120)
            #time.sleep(1/240)#con esto aqui no se recibe nada en el navegador

    # listener    
    async def listen(self, websocket, path):
        '''listenner is called each time new client is connected
        websockets already ensures that a new thread is run for each client'''

        print("listen: ", websocket)
        
        # register new client #
        self.USERS.add(websocket)
        await self.notify_users()

        # this loop to get massage from client #
        while True:
            try:
                msg = await websocket.recv()
                if msg is None:
                    break
                await self.handle_message(msg) #Sergio: he añadido self.client y nada. Funciona: quitado client

            except websockets.exceptions.ConnectionClosed:
                print("close: ", websocket)
                break

        self.USERS.remove(websocket)        
        await self.notify_users()
    
    # message handler        
    async def handle_message(self, data): #Sergio: Funciona: quitado client
        print("handle_message: ", data) #Sergio: Funciona: quitado client

    # example of an action
    # action: notify
    async def notify_users(self):
        '''notify the number of current connected clients'''
        if self.USERS: # asyncio.wait doesn't accept an empty list
            message = json.dumps({'type': 'users', 'count': len(self.USERS)})
            await asyncio.wait([user.send(message) for user in self.USERS])

    # action: action
    async def action(self):
        '''this is an action which will be executed when user presses on button'''
        if self.USERS: # asyncio.wait doesn't accept an empty list
            message = json.dumps({'type': 'activation', 'count':'true'})
            await asyncio.wait([user.send(message) for user in self.USERS])
    
    #Sergio: action: action
    async def action_trackir(self):
        '''Sergio'''
        if self.USERS: # asyncio.wait doesn't accept an empty list
            message = json.dumps({
                'yaw': '00',
                'pitch':'00', 
                'roll':'00'
                })
            await asyncio.wait([user.send(message) for user in self.USERS])

    # expose action
    def do_activate(self):
        '''this method is exposed to outside, not an async coroutine'''
        # use asyncio to run action
        # must call self.action(), not use self.action, because it must be a async coroutine
        asyncio.get_event_loop().run_until_complete(self.action())
    
    #Sergio: expose action
    def do_activate_trackir(self):
        '''Sergio'''
        # use asyncio to run action
        # must call self.action(), not use self.action, because it must be a async coroutine
        asyncio.get_event_loop().run_until_complete(self.action_trackir())


    
################################################################################################################
#MAIN
################################################################################################################

if __name__ == "__main__":    

    #global window
    #window = tkinter.Tk()
    #app = MyWindow(window) #Si esta en otra clase
    window = tkinter.Tk()
    main(window)

    #Threads

    #WebSocketThread
    threadWebSocket = WebSocketThread("WebSocketThread") #Name
    threadWebSocket.start()
    #TrackirThread
    threadTrackir = TrackirThread("TrackirThread") #Name
    threadTrackir.start()
                    
    
    # helper function for window
    '''
    def clicked():
        threadWebSocket.do_activate()
        lbl.configure(text="Button 1 !!") 

    def clicked_trackir():
        threadWebSocket.do_activate_trackir()
        lbl.configure(text="Button 2 !!")           
    '''

    #Ejemplo del Websocket con Threads
    #lbl = tkinter.Label(window, text="Hello")
    #lbl.grid(column=0, row=0)

    '''
    btn = tkinter.Button(window, text="Click Me", command=clicked)
    btn.grid(column=1, row=0)
        
    btn = tkinter.Button(window, text="Click Me", command=clicked_trackir)
    btn.grid(column=1, row=50)
    '''

    window.mainloop()

    

    
  
    
    

   
  
  
  
  
