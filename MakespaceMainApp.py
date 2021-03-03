from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QLineEdit, QLabel, QFileDialog

from MSpace.Login import LoginDialog
from MSpace.DB_Interactions import update_overview, select, get_updated_part_values
from MSpace.DB_Interactions import insert
from MSpace import Globals
from ResourceDir.MakerspaceApp import Ui_MainWindow
from IDGenerator import get_inventory_rid, get_inventory_gid
from FormattedDate import ymd
from UIFunctions import layout_widgets

import ResourceDir.makerspace_resource_rc as resource


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.hide_all()
        self._run_clock()
        self._set_inventory_overview()
        self._set_search_tab()
        self._set_update_inventory_tab()
        self._set_append_tab()

        self.update_date()

        self.inventory_as_admin = None

        # Link approve inventory tab clicked to its tab setup method
        # self.inventory_tab.tabBarClicked(4)

    def update_date(self):
        self.date_label.setText("Today")

    def hide_all(self):
        for i in range(self.verticalLayout_8.count()):
            self.verticalLayout_8.itemAt(i).widget().hide()
        for i in range(self.verticalLayout_9.count()-1):
            self.verticalLayout_9.itemAt(i).widget().hide()
        for i in range(self.verticalLayout_10.count()-1):
            self.verticalLayout_10.itemAt(i).widget().hide()
        for i in range(self.verticalLayout_11.count()-1):
            self.verticalLayout_11.itemAt(i).widget().hide()

    def _set_append_tab(self):
        self.search_file_append_inv.clicked.connect(self.open_file_name_dialog)
        self.check_last_inv_id.clicked.connect(self.show_last_item_id)
        self.search_file_append_inv.clicked.connect(self.openFileNameDialog)

    def openFileNameDialog(self):
        dialog = QFileDialog()
        fname = dialog.getOpenFileName(None, "Import JSON", "", "JSON files (*.json)")
        print(fname)

    def show_last_item_id(self):
        item_group = str(self.choose_item_cat_inv.currentText())
        inventory_key = "%" + Globals.app_data['inventory_item_groups'][item_group] + "%"

        query = "SELECT part_id FROM public.general_inventory WHERE part_id LIKE %s;"
        part_id = select(query, (inventory_key,))

        lpi = [int(x[0][-3:]) for x in part_id]

        try:
            lpi = lpi.index(max(lpi))
            self.last_inv_id_label.setText(part_id[lpi][0])
        except ValueError:
            pass

        if lpi == []:
            next_id = "000" + inventory_key[1:-1] + "001"
            self.last_inv_id_label.setText("ID Has Not Been Used")
        elif 0 < lpi < 9:
            next_id = part_id[lpi][0][:-1] + str(int(part_id[lpi][0][-1]) + 1)
        else:
            next_id = "N/A"
        self.label_51.setText(next_id)

    def open_file_name_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_n, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                "All Files (*);;Python Files (*.py)", options=options)

    def _set_inventory_overview(self):
        output = update_overview()
        self.main_date_label.setText("Week of Monday: " + output[0][0].strftime('%B, %d, %Y'))

        self.cons_value.setText(str(output[0][1]))
        self.item_lost_value.setText(str(output[0][2]))
        self.material_cost_value.setText(str(output[0][3]))
        self.approvals_value.setText(str(output[0][4]))
        self.rejections_value.setText(str(output[0][5]))
        self.total_cost_value.setText(str(output[0][6]))

        staff_names = output[0][9].split(",")
        staff_names_text = ""
        for s in staff_names:
            staff_names_text += s
            staff_names_text += "\n"

        self.current_staff_text_value.setText(staff_names_text)
        self.current_n_of_items_value.setText(str(output[0][7]))
        self.last_update_value.setText(str(output[0][8]))

        self.cost_of_running_value.setText(str(output[0][10]))
        self.revenue_value.setText(str(output[0][11]))
        self.num_staff_value.setText(str(output[0][12]))
        self.num_stud_workers_value.setText(str(output[0][13]))
        self.num_volunteers_value.setText(str(output[0][14]))

        self.next_general_inv_value.setText(str(output[0][15]))

    def _set_search_tab(self):
        self.search_inventory_type.addItem('Machine Shop')
        self.search_inventory_type.addItem('3D Printing')
        self.search_inventory_type.addItem('Soldering Room')
        self.search_inventory_type.addItem('Tool Checkout')
        self.search_inventory_type.addItem('Computers')
        self.search_inventory_type.addItem('General')

        self.search_as_user.setText(Globals.app_data['app_user']['username'])
        self.search_access.setText(str(Globals.app_data['app_user']['access']))

        self.search_button.clicked.connect(self.search_button_clicked)
        self.search_display_table.cellDoubleClicked.connect(self.send_search2update)

    def search_button_clicked(self):
        try:
            self.search_display_table.setRowCount(0)
            group = self.search_inventory_type.currentText()
            n_entries = self.search_number_of_entries.value()

            key = '%' + str(self.search_keyword.text().strip()) + "%"
            if key == '':
                raise TypeError
            self.search_keyword.clear()

            as_partid = self.search_checkbox_keyword_as.isChecked()
            sum_res = self.search_checkbox_return_summary.isChecked()
            bfit = self.search_checkbox_best_fit.isChecked()

            Globals.groups = {"Machine Shop": '1.150MSMR0',
                              '3D Printing': '1.150F3DPR',
                              'Soldering Room': '1.150SR000',
                              'Tool Checkout': '1.150BTCR0',
                              'Computers': '1.150MSPCE',
                              'General': 'MAKERSPACE'}

            if as_partid:
                asql = ("SELECT part_id, name, location_id, qty, available_to_rent, who_has_it "
                        "FROM public.general_inventory "
                        "WHERE (general_inventory.group_serial = %s AND "
                        "(part_id LIKE %s "
                        "OR description LIKE %s "
                        "OR location_id LIKE %s)) "
                        )
                params = [Globals.groups[group], key.upper(), key, key]
            else:
                asql = ("SELECT part_id, name, location_id, qty, available_to_rent, who_has_it "
                        "FROM public.general_inventory "
                        "WHERE (general_inventory.group_serial = %s AND "
                        "(name LIKE %s "
                        "OR description LIKE %s "
                        "OR location_id LIKE %s)) "
                        )
                params = [Globals.groups[group], key, key, key]

            results = select(asql, params)

            if self.search_checkbox_best_fit.checkState() == 2:
                results = results[0]
                self.search_display_table.setRowCount(self.search_display_table.rowCount() + 1)
                for its in range(len(results)):
                    self.search_display_table.setItem(self.search_display_table.rowCount() - 1, its,
                                                      QTableWidgetItem(str(results[its])))
            elif len(results) > n_entries:
                results = results[:n_entries]
                if n_entries == 1:
                    results = results[0]

                for k in range(len(results)):
                    self.search_display_table.setRowCount(self.search_display_table.rowCount() + 1)
                    for its in range(len(results[k])):
                        self.search_display_table.setItem(self.search_display_table.rowCount() - 1, its,
                                                          QTableWidgetItem(str(results[k][its])))
            else:
                for k in range(len(results)):
                    self.search_display_table.setRowCount(self.search_display_table.rowCount() + 1)
                    for its in range(len(results[k])):
                        self.search_display_table.setItem(self.search_display_table.rowCount() - 1, its,
                                                          QTableWidgetItem(str(results[k][its])))

        except TypeError:
            pass

    def _set_update_inventory_tab(self):
        self.update_veriffy_button.clicked.connect(self.verify_button_inventory)
        self.update_show_entries_button.clicked.connect(self.show_entries_button_inventory)
        self.update_send_button.clicked.connect(self.send_update_2_revision_inventory)
        self.update_activate_button.clicked.connect(self.inventory_admin_override)

        Globals.inventory_override_query_table = 'private.inventory_approvals'
        self.update_admin_label.setText('Enter Admin Code')

    def send_update_2_revision_inventory(self):
        # When linked button is clicked the application sends current information in entries to database and
        # create a new request ID entry in inventory_update_request table. This table should have the information
        # that goes into inventory approvals tab table
        request_id = get_inventory_rid()
        group_id = get_inventory_gid()
        date_sub = ymd()
        line_update = 0
        name = Globals.app_data['app_user']['username']
        reviewed = False
        s = ''

        lays = [self.verticalLayout_8, self.verticalLayout_9, self.verticalLayout_10, self.verticalLayout_11]

        params = [request_id, date_sub, name, line_update, reviewed, group_id]
        nparams = []
        for g in lays:
            for w in layout_widgets(g):
                if isinstance(w, QLineEdit):
                    if not w.text():
                        pass
                    else:
                        params.append(w.text())
                        nparams.append(w.text())
                if isinstance(w, QLabel):
                    if w.text() == 'TextLabel':
                        pass
                    else:
                        s += str(w.text()) + ', '

        params[13:15] = [int(x) for x in params[13:15]]
        nparams[7:9] = [int(x) for x in nparams[7:9]]

        try:
            params[11:13] = [int(x) for x in params[11:13]]
            nparams[5:7] = [int(x) for x in nparams[5:7]]
        except ValueError:
            if params[11] == 'None':
                params[11] = None
                nparams[5] = None
            if params[12] == 'None':
                params[12] = None
                nparams[6] = None

        if params[15] == 'True':
            params[15] = True
            nparams[9] = True
        if params[16] == 'False':
            params[16] = False
            nparams[10] = True

        params = tuple(params)

        s = s[:-2] + ')'

        if Globals.inventory_override_query_table == 'public.general_inventory':
            nparams.append(self.update_entry_1.text())
            nparams = tuple(nparams)
            query = ("""UPDATE {} """
                     """SET part_id = %s, """
                     """name = %s, """
                     """description = %s, """
                     """location_id = %s, """
                     """group_serial = %s, """
                     """device_serial = %s, """
                     """utsa_asset_id = %s, """
                     """training_lvl = %s, """
                     """qty = %s, """
                     """available_to_rent = %s, """
                     """in_maintenance = %s, """
                     """who_has_it = %s """
                     """WHERE part_id = %s""".format(Globals.inventory_override_query_table))
            insert(query, nparams)
        else:
            query = ("""INSERT INTO {} (request_id, date_submitted, submitter, lines_updated, """
                     """reviewed, group_id, {} VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, """
                     """%s, %s, %s, %s, %s, %s, %s, %s, %s);""".format(Globals.inventory_override_query_table, s))

            insert(query, params)

            params = (request_id, date_sub, name, line_update, reviewed, group_id)
            query = ("INSERT INTO private.inventory_update_request (request_id, date_submitted, submitter, "
                     "lines_updated, reviewed, group_id) VALUES (%s, %s, %s, %s, %s, %s); ")
            insert(query, params)
        Globals.inventory_override_query_table = 'private.inventory_approvals'

    def verify_button_inventory(self):
        try:
            self.update_resulting_part_name.setText(Globals._name_)
        except AttributeError:
            pass

    def inventory_admin_override(self):
        key = self.update_entry_override.text()

        query = "SELECT override FROM private.overrides_inventory WHERE override = %s;"
        params = (key,)

        try:
            o = select(query, params)
            if o[0][0] == key:
                Globals.inventory_override_query_table = 'public.general_inventory'
                self.update_admin_label.setText('Updating as Admin')
            else:
                raise ValueError
        except ValueError:
            self.update_admin_label.setText('Unsuccessful Admin Override')

    def show_entries_button_inventory(self):
        try:
            # Get columns
            key = self.update_part_id.text().strip().upper()
            group = self.search_inventory_type.currentText()    # Save this in json app state file for future use

            get_updated_part_values(group, key)

            if len(Globals.inventory_entries_vals) > 8:
                for i in range(9):
                    self.verticalLayout_8.itemAt(i).widget().setText(str(Globals.inventory_entries_cols[i]))
                    self.verticalLayout_8.itemAt(i).widget().show()
                for i in range(9):
                    self.verticalLayout_9.itemAt(i).widget().setText(str(Globals.inventory_entries_vals[i]))
                    self.verticalLayout_9.itemAt(i).widget().show()
                for i in range(0, len(Globals.inventory_entries_vals) - 9):
                    self.verticalLayout_10.itemAt(i).widget().setText(str(Globals.inventory_entries_cols[i + 9]))
                    self.verticalLayout_10.itemAt(i).widget().show()
                for i in range(0, len(Globals.inventory_entries_vals) - 9):
                    self.verticalLayout_11.itemAt(i).widget().setText(str(Globals.inventory_entries_vals[i + 9]))
                    self.verticalLayout_11.itemAt(i).widget().show()
            else:
                for i in range(len(Globals.inventory_entries_vals)):
                    self.verticalLayout_10.itemAt(i).widget().setText(str(Globals.inventory_entries_cols[i]))
                    self.verticalLayout_10.itemAt(i).widget().show()

                for i in range(len(Globals.inventory_entries_vals)):
                    self.verticalLayout_11.itemAt(i).widget().setText(str(Globals.inventory_entries_vals[i]))
                    self.verticalLayout_11.itemAt(i).widget().show()

        except AttributeError:
            pass

    def send_search2update(self, row, column):
        if column == 0:
            item = self.search_display_table.item(row, column)
            name = self.search_display_table.item(row, column + 1)
            Globals._name_ = name.text()
            self.update_part_id.setText(item.text())

    def _run_clock(self):
        # creating a timer object
        timer = QTimer(self)

        # adding action to timer
        timer.timeout.connect(self._update_clock)

        # update the timer every second
        timer.start(1000)

    def _update_clock(self):
        # getting current time
        current_time = QTime.currentTime()

        # converting QTime object to string
        label_time = current_time.toString('h:mm:ss:AP')

        # showing it to the label
        self.time_label.setText(label_time)


if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginDialog()

    if login.exec_() == QtWidgets.QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
