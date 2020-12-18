import sys
import cv2
import threading
#!pip install SpeechRecognition
import speech_recognition as sr
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5.QtCore import *
import time
import numpy as np
import matplotlib.pyplot as pp
import requests
from gtts import gTTS
from playsound import playsound
import pandas as pd

ip_address = "http://127.0.0.1:5000" # 라지베리파이에 넣을 때 노트북 IP로 바꿔야 함.
# model = tf.keras.models.load_model('model_31.h5',custom_objects={'KerasLayer':hub.KerasLayer})
# model.summary()
# model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy']), compile=False
# category_list=pd.Series(pd.read_csv('category_list_31.txt')['0'])

word_dict=pd.read_csv('단어감지.csv',encoding='euc-kr',index_col='기본')
compound_list=pd.DataFrame(index=['두어요'],columns=['앞단어','합성어'])
compound_list.loc['두어요']=['살펴요','보관해요']

word_list=[]
n= 0
def end():
    global n
    global word_list
    global word_dict
    
    if word_dict['과거'][word_list[n-2]]!='0':
        word_list[n-2]=word_dict['과거'][word_list[n-2]]
        del word_list[n-1]
        n=n-1
    
    st=''    
    for i in word_list:
            st=st+ i+' '   
    return st
        
def ing():
    global n
    global word_list
    global word_dict
    if word_dict['하는'][word_list[n-2]]!='0':
        word_list[n-2]=word_dict['하는'][word_list[n-2]]
        word_list[n-1]='중이에요'
        n=n-1
    
    st=''    
    for i in word_list:
            st=st+ i+' '   
    return st

def none():
    global word_list
    word_list=[]

def compound():
    global n
    global word_list
    global compound_list
    
    if word_list[n-1] in compound_list.index:
        word_list[n-2]=compound_list['합성어'][word_list[n-1]]
        del word_list[n-1]
        n=n-1
        
    st=''    
    for i in word_list:
            st=st+ i+' '   
    return st    
func_dict={
        '도중이에요' : ing,
        '끝나요' : end,
        '없음' : none
        }
def make_sentence(word):
    global n
    word_list.append(word)
    n=len(word_list)
    
    if len(word_list)==1:
        return word
    else: 
        x=word_list[n-1]
        if x in func_dict:
            result=func_dict[x]()
        else: 
            result=compound()
        
        return result

class SignRecognition(QObject):
    signal1 = pyqtSignal(int)
    def __init__(self, label, label2, label3, probar):
        QObject.__init__(self)
        self.label = label
        self.label2 = label2 
        self.label3 = label3
        self.probar = probar
        self.running = False

    def tts(self, str): # str에 적힌 내용을 tts로 읽어주는 함수
        tts = gTTS(text=str, lang='ko')
        tts.save("temp.mp3")
        playsound("temp.mp3")

    def crop_center_square(self, frame):
         y, x = frame.shape[0:2]
         min_dim = min(y, x)
         start_x = (x // 2) - (min_dim // 2)
         start_y = (y // 2) - (min_dim // 2)
         frame= frame[start_y:start_y+min_dim,start_x:start_x+min_dim]

         # frame = frame[ :, [2, 1, 0]]
         
         return frame

    def predict(self,data):
        # print(data)
        upload= {'file':data}
        res = requests.post(ip_address + "/video", files=upload)
        return res.json()
    
    def run(self):
        label_text = self.label3.text()
        cap = cv2.VideoCapture(0)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.label.resize(141, 141)
        frames=[]
        cnt = 0
        self.signal1.emit(cnt)
        while self.running:
            ret, img = cap.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                img= self.crop_center_square(img)
                temp_img= cv2.resize(img, (141, 141))
                
                h,w,c = temp_img.shape
                qImg = QtGui.QImage(temp_img.data.tobytes(), h,w, w*c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                self.label.setPixmap(pixmap)
                time.sleep(1/30)

                img= cv2.resize(img, (224, 224))
                frames.append(img)
                cnt+=1
                self.signal1.emit(cnt)
                #print(cnt)
                if cnt == 60:
                    cnt = 0
                    frames=(np.array(frames)).reshape(-1,60,224,224,3) /255.0
                    pred=self.predict(frames)
                    if pred == "없음":
                        self.label3.setText(label_text + "\n")
                        label_text = self.label3.text()
                    self.label3.setText(label_text+ "수어: "+ make_sentence(pred))
                    self.label2.setText(pred)
                    frames=[]
            else:
                print("cannot read frame.")
                break
        cap.release()
        self.label3.setText(label_text + "\n")
        self.label.clear()
        self.label2.clear()
        self.probar.hide()
        print("Thread end.")

    def isRunning(self):
        return self.running

    def stop(self):
        self.running = False
        print("stoped..")

    def start(self):
        self.running = True
        th = threading.Thread(target=self.run)
        th.start()
        print("started..")

    def onExit(self):
        print("exit")
        stop()
    
class SpeechRecognition():
    def __init__(self, label):
        self.label = label
        self.running = False

    def run(self):
        AUDIO_FILE = "hello.wav"

        # audio file을 audio source로 사용합니다
        r = sr.Recognizer()
        m = sr.Microphone()
        with m as source: r.adjust_for_ambient_noise(source)
        print("energy threshold: %d" % r.energy_threshold)
        while self.running:
            #with sr.AudioFile(AUDIO_FILE) as source:
            #audio = r.record(source)  # 전체 audio file 읽기
            
            print("Say something.")
            with m as source: audio = r.listen(source)
            label_text = self.label.text()
            if not self.running:
                print("sorry, speech recognition service is closed")
                break
            self.label.setText(label_text + "구어: ...\n")
            print("Got it, Recognizing it...")
            # 구글 웹 음성 API로 인식하기 (하루에 제한 50회)
            try:
                recog_result = r.recognize_google(audio, language='ko')
                print("Google Speech Recognition thinks you said : " + recog_result)
                self.label.setText(label_text + "구어: " + recog_result  + "\n")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                self.label.setText(label_text)
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
                self.label.setText(label_text)
        print("Thread end.")

    def isRunning(self):
        return self.running

    def stop(self):
        self.running = False
        print("stoped..")

    def start(self):
        self.running = True
        th = threading.Thread(target=self.run)
        th.start()
        print("started..")

    def onExit(self):
        print("exit")
        stop()
#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("CDE.ui")[0]
#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.sign_recog = SignRecognition(self.label,self.label_3, self.label_2, self.probar)
        self.speech_recog = SpeechRecognition(self.label_2)
        self.scrollArea.setWidget(self.label_2)
        self.probar.hide()
        #버튼에 기능을 연결하는 코드
        self.btn_1.clicked.connect(self.button1Function)
        self.btn_2.clicked.connect(self.button2Function)
        self.btn_3.clicked.connect(self.button3Function)
        #self.label_2.setText("a\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\na\n")
        print(self.scrollArea.verticalScrollBar().maximum())
        self.scrollArea.verticalScrollBar().setValue(2)
        self.sign_recog.signal1.connect(self.signal1_emitted)

    @pyqtSlot(int)
    def signal1_emitted(self, value):
        self.probar.setValue(value)

    def button1Function(self) :
        if not self.sign_recog.isRunning():
            self.sign_recog.start()
            self.probar.show()
            self.btn_1.setStyleSheet('color: red')
            self.btn_1.setText("수어 영상 중단")
        else:
            self.sign_recog.stop()
            self.btn_1.setStyleSheet('color: black;')
            self.btn_1.setText("수어 영상 시작")

    def button2Function(self) :
        if not self.speech_recog.isRunning():
            self.speech_recog.start()
            self.btn_2.setStyleSheet('color: red;')
            self.btn_2.setText("마이크 중단")
        else:
            self.speech_recog.stop()
            self.btn_2.setStyleSheet('color: black;')
            self.btn_2.setText("마이크 시작")

    def button3Function(self):
        fname = QFileDialog.getExistingDirectory(self, 'Find Folder')
        if fname == "": return
        with open(fname + "/" + "회의록.txt", "wt") as fp:
            fp.write(self.label_2.text())

if __name__ == "__main__" :
    app = QApplication(sys.argv) 
    myWindow = WindowClass() 
    myWindow.show()
    app.exec_()