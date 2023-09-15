import pickle
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton,QHBoxLayout, QVBoxLayout, QWidget, QLabel, QMessageBox,QFileDialog, QInputDialog,QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap
import socket
from utils.uitls import *
import threading
import pandas as pd
from io import BytesIO 
# 服务器主机和端口
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

# 创建客户端套接字以连接服务器
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
df_global = pd.DataFrame()

class LoginWindow(QMainWindow):
    """
        这里是登陆界面
    """
    def __init__(self):
        super().__init__()
       
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 150)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 页面控件
        self.connect_label = QLabel("connecting...")
        self.account_label = QLabel("Enter Account:")
        self.account_input = QLineEdit()
        self.login_button = QPushButton("Login")
        self.btn_register = QPushButton("Register a new account")

        # 布局
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.connect_label)
        self.layout.addWidget(self.account_label)
        self.layout.addWidget(self.account_input)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.btn_register)
        self.central_widget.setLayout(self.layout)

        # 槽函数
        self.login_button.clicked.connect(self.login)
        self.btn_register.clicked.connect(self.register_newaccount)

        # 其他属性
        self.personal_info = pd.DataFrame() # 客户端临时df，用来检索人员信息

        # 初始化
        self.connect_to_server()
        self.request_personal_info()
        
    def connect_to_server(self):
        # 客户端尝试连接服务器
        try:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("连接成功")
            self.connect_label.setText("connected!")
        except ConnectionRefusedError:
            print("连接被拒绝")
        except socket.timeout:
            print("连接超时")
        except Exception as e:
            print(f"连接错误: {e}")
    
    def request_personal_info(self):
        # 向服务器申请人员信息
        client_socket.send(b"LOGIN_REQUEST_PERSONAL_INFO / HTTP/1.1")
        receive_data = b''
        while True:
            data_chunk = client_socket.recv(1024)
            receive_data += data_chunk
            if b'EOF' in data_chunk:
                break
        receive_data = receive_data[:-3]
        # 将bits数据流转换为csv，再读取得到df对象
        df_global = pd.read_excel(BytesIO(receive_data))
        self.personal_info = df_global




    def login(self):
        account = self.account_input.text().strip()
        if account in self.personal_info['账号'].values:
            if account.startswith("t"):
                self.openSubpage1()
            elif account.startswith("s"):
                self.openSubpage2()
            elif account.startswith("a"):
                self.openSubpage3()
            else:
                QMessageBox.warning(self.central_widget, 'warning', 'Please input right id!')
                self.account_input.clear()
        else:
            QMessageBox.warning(self.central_widget, 'warning', 'Please input right id!')
            self.account_input.clear()

    def openSubpage1(self):
        subpage1 = Subpage1()
        self.setCentralWidget(subpage1)
        self.setWindowTitle("欢迎你，老师！")

    def openSubpage2(self):
        subpage2 = Subpage2()
        self.setCentralWidget(subpage2)
        self.setWindowTitle("欢迎你，同学！")

    def openSubpage3(self):
        subpage3 = Subpage3(self.personal_info)
        self.setCentralWidget(subpage3)
        self.setWindowTitle("欢迎你，管理员！")
    def register_newaccount(self):
        account = self.account_input.text().strip

class Subpage1(QWidget):
    """
    教师客户端，需要实时监听服务器传来的消息
    """
    def __init__(self):
        super().__init__()
        # 页面布局
        self.setWindowTitle("教师客户端")
        self.setGeometry(100, 100, 400, 150)
        # 页面内控件
        label = QLabel("Welcome to 教师客户端!")
        self.homework_image = ""
        self.homework_pix = QLabel(self)
        self.btn_upload_Video = QPushButton("点击上传视频")
        self.btn_download_homework = QPushButton("点击下载作业")
        self.btn_upload_read_homework = QPushButton("上传批阅后的作业")

        # 布局
        self.layout = QVBoxLayout()
        self.layout.addWidget(label)
        self.layout.addWidget(self.homework_pix )
        self.layout.addWidget(self.btn_upload_Video)
        self.layout.addWidget(self.btn_download_homework)
        self.layout.addWidget(self.btn_upload_read_homework)


        self.setLayout(self.layout)

        # 槽函数
        self.btn_upload_Video.clicked.connect(self.upload_video)
        self.btn_download_homework.clicked.connect(self.download_homework)
        self.btn_upload_read_homework.clicked.connect(self.upload_read_homework)
        # 其他属性
        self.read_homework = Homework()
        # self.lisening_thread = QThread()

    def receive_homeworks(self):
        pass

    def eidt_and_upload_homework(self):
        pass

    def upload_video(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "",
                                                   "All Files (*);;Text Files (*.txt);;Image Files (*.png *.jpg)",
                                                   options=options)
        if file_name:
            client_socket.send(b"TEACHER_POST_VIDEO / HTTP/1.1")
            with open(file_name, "rb") as video_file:
                video_data = video_file.read()
                video_data = video_data + b"EOF" # 给数据流加上结束标志，以与接收端协议何时结束
                client_socket.send(video_data)
            print("已上传视频文件")
    
    def download_homework(self):
        client_socket.send(b"TEACHER_GET_HOMEWORK / HTTP/1.1")
        homework_data = b""
        while True:
            data_chunk = client_socket.recv(1024)
            homework_data += data_chunk
            if b"EOF" in data_chunk:
                break
        homework_data = homework_data[:-3]
        self.read_homework = pickle.loads(homework_data)  # 将数据流解码为homework对象
        file_dir = "client_data/homework.jpg"
        with open(file_dir, "wb") as file:
            file.write(self.read_homework.content)
            self.homework_image = QPixmap(file_dir)
        print("下载作业成功")
        self.homework_pix.setPixmap(self.homework_image)

        # 批阅作业
        comment , ok = QInputDialog.getText(self,"批阅","输入要批阅的内容")
        self.read_homework.edit(comment=comment,goal=100)
    def upload_read_homework(self): 
        # 上传批阅后的作业
        homework_data = pickle.dumps(self.read_homework)
        homework_data += b"EOF"
        
        # 这里出现的问题在服务器，由于未开启多线程，服务器只监听一次，也就是说第二次的send服务器是接收不到的（服务器处理完一个elif就退出去了）
        client_socket.send(b"TEACHER_POST_HOMEWORK_READ / HTTP/1.1")
        client_socket.send(homework_data)
        print("执行了上传")

class Subpage2(QWidget):
    """
        这里是学生客户端页面
    """
    def __init__(self):
        super().__init__()
        # 页面布局
        self.setWindowTitle("学生客户端")
        self.setGeometry(100, 100, 400, 150)
        # 页面内控件
        self.btn_upload_homework = QPushButton('upload homework')
        self.btn_download_jiaoxuevideo = QPushButton("download jiaoxuevideo")
        self.btn_download_readhomework = QPushButton("download read homework")
        label = QLabel("Welcome to 学生客户端!")
        self.label_homework_comment = QLabel()

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.label_homework_comment)
        layout.addWidget(self.btn_upload_homework)
        layout.addWidget(self.btn_download_readhomework)
        layout.addWidget(self.btn_download_jiaoxuevideo)
        self.setLayout(layout)

        # 槽函数
        self.btn_upload_homework.clicked.connect(self.upload_homework)
        self.btn_download_jiaoxuevideo.clicked.connect(self.download_vedios)
        self.btn_download_readhomework.clicked.connect(self.download_readhomework)

        # 其他属性
        self.homework = Homework() #------------------bug

    def upload_homework(self):
        # 选择作业文件
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "",
                                                   "All Files (*);;Text Files (*.txt);;Image Files (*.png *.jpg)",
                                                   options=options)
        # 读取作业文件为数据流，便于封装为类
        with open(file_name, 'rb') as homework_file:
            homework_data = homework_file.read()
            self.homework.change_data(homework_data)
        # 将作业对象绑定作业数据流,并将作业对象化为字节流，便于传输

        homework_data = pickle.dumps(self.homework)
        homework_data = homework_data + b"EOF"

        if file_name:
            client_socket.send(b"STUDENT_POST_HOMEWORK / HTTP/1.1")
            client_socket.send(homework_data)
            QMessageBox.information(self, "information", f"上传作业：{file_name}")


    def download_vedios(self):
        pass
        client_socket.send(b"STUDENT_GET_VIDEO / HTTP/1.1")
        download_vedio_data = b""
        while True:
            data_chunk = client_socket.recv(1024)
            download_vedio_data += data_chunk
            if b"EOF" in data_chunk:
                break
        download_vedio_data = download_vedio_data[:-3]
        with open("client_data/jiaoxue_video.mp4", "wb") as jiaoxue_video:
            jiaoxue_video.write(download_vedio_data)
        print(f"下载视频成功！")

    def download_readhomework(self):
        client_socket.send(b"STUDENT_GET_HOMEWORK_READ / HTTP/1.1")
        download_homework_data = b""
        while True:
            data_chunk = client_socket.recv(1024)
            download_homework_data += data_chunk
            if b"EOF" in data_chunk:
                break
        download_homework_data = download_homework_data[:-3]
        with open("client_data/homeworks_read/homework_read.bin", "wb") as file:
            file.write(download_homework_data)
        homework_read =  pickle.loads(download_homework_data)
        self.label_homework_comment.setText(f"老师给你的批语：{homework_read.comment}")
        print(f"查看作业成功！")

class Subpage3(QWidget):
    """
        这里是管理员界面
    """
    def __init__(self,personal_info):
        super().__init__()
        # 页面布局
        self.setWindowTitle("管理员客户端")
        self.setGeometry(100, 100, 400, 150)

        # 页面控件 
        self.label_intro = QLabel("欢迎您！")
        self.btn_view = QPushButton("点击查看人员信息")
        self.tabel_personal_infor = QTableWidget()
        

        # 布局
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.btn_view)
        self.setLayout(self.layout)

        # 槽函数
        self.btn_view.clicked.connect(self.view_personal_infor)
        # 其他属性
        self.personal_info = personal_info
        self.table_window = TableViewer(self.personal_info)
        # 初始化

    def view_personal_infor(self):
        # 这里注意，如果是在该函数里创建窗口对象，那么该窗口对象的生命周期就是该函数的运行周期，生命周期结束，对象消失，会导致窗口闪退
        self.table_window.show()
        
class TableViewer(QMainWindow):
    """
        这里是表格界面
    """
    def __init__(self, personal_info):
        super().__init__()
        self.personal_info = personal_info
        self.current_df = self.personal_info
        self.initUI()

    def initUI(self):
        self.setWindowTitle('表格信息查看器')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.lineedit_exact = QLineEdit("输入账号精确查询：")
        self.lineedit_blurry = QLineEdit("输入姓名模糊查询")
        self.btn_search = QPushButton("精确查询")
        self.btn_search_blurry = QPushButton("模糊查询")
        self.combobox_choose_arg = QComboBox(self)
        self.label_choose_feature = QLabel("选择排序特征:")
        for index in self.personal_info.columns.tolist():
            self.combobox_choose_arg.addItem(str(index))
        self.table_widget = QTableWidget()
        # 布局
        self.layout = QVBoxLayout()
        self.hor_box0 = QHBoxLayout()
        self.hor_box0.addWidget(self.lineedit_exact)
        self.hor_box0.addWidget(self.lineedit_blurry)
        self.layout.addLayout(self.hor_box0)
        self.hor_box1 = QHBoxLayout()
        self.hor_box1.addWidget(self.label_choose_feature)
        self.hor_box1.addWidget(self.combobox_choose_arg)

        self.hor_box2 = QHBoxLayout()
        self.hor_box2.addWidget(self.btn_search)
        self.hor_box2.addWidget(self.btn_search_blurry)
        self.layout.addLayout(self.hor_box1)
        self.layout.addLayout(self.hor_box2)
        self.layout.addWidget(self.table_widget)
        
        
        
        self.central_widget.setLayout(self.layout)

        # 槽函数
        self.btn_search.clicked.connect(self.present_choosed)
        self.btn_search_blurry.clicked.connect(self.present_choosed_blurry)
        self.combobox_choose_arg.currentTextChanged.connect(self.sort)
        # 其他属性

        # 初始化
        self.populateTable()

    

    def populateTable(self,data = None):
        if data is None:
            data = self.current_df
        self.table_widget.setColumnCount(data.shape[1])
        self.table_widget.setRowCount(data.shape[0])
        # self.table_widget.setHorizontalHeaderLabels(["First Name", "Last Name", "Email"])
        self.table_widget.setHorizontalHeaderLabels(data.columns.tolist())
        for i in (range(data.shape[0])):
            for j in range(data.shape[1]):
                item = QTableWidgetItem(str(data.iloc[i,j]))
                self.table_widget.setItem(i, j, item)

    def present_choosed(self):
        if self.lineedit_exact.text():
            self.table_widget.clearContents()
            index = self.lineedit_exact.text().strip()
            self.current_df = self.personal_info[self.personal_info['账号'].str.contains(index, case=False)]
            self.populateTable(self.current_df)
        else:
            QMessageBox.warning(self.central_widget, 'warning', '精确查询条件为空，请输入内容！')

    def present_choosed_blurry(self):
        if self.lineedit_blurry.text():
            self.table_widget.clearContents()
            index = self.lineedit_blurry.text().strip()
            self.current_df = self.personal_info[self.personal_info['姓名'].str.contains(index, case=False)]
            self.populateTable(self.current_df)
        else:
            QMessageBox.warning(self.central_widget, 'warning', '模糊查询条件为空，请输入内容！')

    def sort(self):
        selected_item = self.combobox_choose_arg.currentText()
        self.current_df = self.current_df.sort_values(by=selected_item, ascending=False)
        self.populateTable(self.current_df)
    
    
    def closeEvent(self, event):
            
            event.accept()




def main():
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
