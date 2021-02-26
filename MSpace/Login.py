import json

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap

from MSpace.DB_Interactions import select
from MSpace import Globals

import ResourceDir.makerspace_resource_rc


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)

        # Label to put the Makerspace Logo
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setPixmap(QPixmap(":/utsa_brand/Makerspace-Logo-scaled.png"))
        self.logo_label.setScaledContents(True)

        # Username label and entry
        self.user_label = QtWidgets.QLabel("Username")
        self.textName = QtWidgets.QLineEdit(self)
        # Password label and entry
        self.password_label = QtWidgets.QLabel("Password")
        self.textPass = QtWidgets.QLineEdit(self)
        self.textPass.setEchoMode(QtWidgets.QLineEdit.Password)

        # Login button linked to handle_login method
        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handle_login)

        # Add widgets to layouts
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.logo_label)
        layout.addWidget(self.user_label)
        layout.addWidget(self.textName)
        layout.addWidget(self.password_label)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)

    def handle_login(self):
        query = f'''SELECT * FROM private.login_credentials WHERE username = %s;'''
        params = (self.textName.text(),)

        output = select(query, params)

        try:
            if output[0][1] == self.textPass.text():
                self.accept()

                a_file = open("ResourceDir/app_data.json", "r")
                Globals.app_data = json.load(a_file)
                a_file.close()

                Globals.app_data["app_user"]['username'] = output[0][0]
                Globals.app_data["app_user"]['access'] = output[0][2]

                a_file = open("ResourceDir/app_data.json", "w")
                json.dump(Globals.app_data, a_file, sort_keys=True, indent=4, separators=(',', ': '))
                a_file.close()

            else:
                QtWidgets.QMessageBox.warning(
                    self, 'Error', 'Bad user or password')
        except IndexError as error:
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Bad user or password')
