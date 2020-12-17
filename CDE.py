import sys
import cv2
import threading
#!pip install SpeechRecognition
import speech_recognition as sr
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5 import QtCore
import time
import numpy as np
import matplotlib.pyplot as pp
import requests

ip_address = "http://127.0.0.1:5000" # 라지베리파이에 넣을 때 노트북 IP로 바꿔야 함.
# model = tf.keras.models.load_model('model_31.h5',custom_objects={'KerasLayer':hub.KerasLayer})
# model.summary()
# model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy']), compile=False
# category_list=pd.Series(pd.read_csv('category_list_31.txt')['0'])

class SignRecognition:
    def __init__(self, label, label2, label3):
        self.label = label
        self.label2 = label2 
        self.label3 = label3
        self.running = False

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
        cap = cv2.VideoCapture(0)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.label.resize(141, 141)
        frames=[]
        cnt = 0
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

                self.label2.setText(str(2 - cnt/30)[:3])
                img= cv2.resize(img, (224, 224))
                frames.append(img)
                cnt+=1
                #print(cnt)
                if cnt == 60:
                    cnt = 0
                    frames=(np.array(frames)).reshape(-1,60,224,224,3) /255.0
                    label_text = self.label3.text()
                    self.label3.setText(label_text + "수어: ...\n")
                    pred=self.predict(frames)
                    self.label3.setText(label_text+ "수어:"+ pred  + "\n")
                    frames=[]
            else:
                print("cannot read frame.")
                break
        cap.release()
        self.label.clear()
        self.label2.clear()
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
            self.label.setText(label_text + "구어: ...\n")
            if not self.running:
                print("sorry, speech recognition service is closed")
                break
            print("Got it, Recognizing it...")
            # 구글 웹 음성 API로 인식하기 (하루에 제한 50회)
            try:
                recog_result = r.recognize_google(audio, language='ko')
                print("Google Speech Recognition thinks you said : " + recog_result)
                self.label.setText(label_text + "구어: " + recog_result  + "\n")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
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
        self.sign_recog = SignRecognition(self.label,self.label_3, self.label_2)
        self.speech_recog = SpeechRecognition(self.label_2)
        self.scrollArea.setWidget(self.label_2)
        #버튼에 기능을 연결하는 코드
        self.btn_1.clicked.connect(self.button1Function)
        self.btn_2.clicked.connect(self.button2Function)
        self.btn_3.clicked.connect(self.button3Function)

    #btn_1이 눌리면 작동할 함수
    def button1Function(self) :
        if not self.sign_recog.isRunning():
            self.sign_recog.start()
            self.btn_1.setStyleSheet('color: red')
            self.btn_1.setText("수어 영상 중단")
        else:
            self.sign_recog.stop()
            self.btn_1.setStyleSheet('color: black;')
            self.btn_1.setText("수어 영상 시작")

    #btn_2가 눌리면 작동할 함수
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
        fileDailog = QFileDialog(self)
        fileDailog.setFileMode(QFileDialog.Directory)
        file_path = fileDailog.getOpenFileName()[0]
        if file_path == "": return
        print(file_path)
        with open(file_path + "/" + "회의록.txt") as fp:
            fp.write(self.label_2.text())

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = WindowClass() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()