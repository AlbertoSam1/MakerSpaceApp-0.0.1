from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QTime, QDate
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QLineEdit, QLabel, QMessageBox

from MSpace.Login import LoginDialog
from MSpace.FileManager import OpenFile
from MSpace.DB_Interactions import update_overview, select, get_updated_part_values
from MSpace.DB_Interactions import insert, delete
from MSpace import Globals
from ResourceDir.MakerspaceApp import Ui_MainWindow
from IDGenerator import get_inventory_rid, get_inventory_gid
from FormattedDate import ymd, year
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
        self._set_machine_shop_safety_training_tab()
        self._set_approve_inventory_tab()
        self._set_conference_r_reservations()

        self.update_date()

        self.inventory_as_admin = None

        # Link approve inventory tab clicked to its tab setup method
        # self.inventory_tab.tabBarClicked(4)

    def _set_conference_r_reservations(self):
        now = QDate.currentDate()
        max_date = now.addDays(31)
        self.conference_calendar.setMaximumDate(max_date)
        self.conference_calendar.setMinimumDate(now)
        self.current_date_label.setText(self.conference_calendar.selectedDate().toString())
        self.conference_calendar.clicked.connect(self.conference_room_calendar_clicked)
        self.conference_student_info.setCurrentIndex(1)
        self.conference_reserve_button.clicked.connect(self.conference_room_reserve_button)

    def conference_room_calendar_clicked(self):
        date = self.conference_calendar.selectedDate()
        self.current_date_label.setText(date.toString())

    def conference_room_reserve_button(self):
        self.conference_student_info.setCurrentIndex(0)

    def update_date(self):
        self.date_label.setText("Today")

    def _set_machine_shop_safety_training_tab(self):
        self.MS_ST_add_student_button.clicked.connect(self._ms_safety_add)
        self.MS_ST_search_trainee_button.clicked.connect(self._ms_safety_search)
        self.MS_ST_add_student_full_name_entry.setText("First, Last")
        self.MS_ST_search_trainee_clear.clicked.connect(self._clear_search_ms_record_window)
        self.MS_ST_search_trainee_renew.clicked.connect(self.renew_ms_safety_training)

    def renew_ms_safety_training(self):
        if self.MS_ST_search_trainee_override_entry.text() == 'OXSDR':
            t = self.MS_ST_search_trainee_textbrowser.toPlainText().split("\n")
            abc123 = t[4][17:-1]
            date = QDate.currentDate().toString().split(" ")[3]
            new_date = QDate.currentDate().addYears(2).toString().split(" ")[3]

            query = ("""UPDATE staff."SafetyTraining-MS" """
                     """SET year_of_com = %s """
                     """WHERE abc123 = %s""")

            params = [date, abc123]

            insert(query, params)

            msg = QMessageBox()
            msg.setWindowTitle("Information")
            msg.setIcon(QMessageBox.Information)
            msg.setText("You have successfully renewed {} expiration of training to {}".format(t[3][6:-1], new_date))
            msg.setStandardButtons(QMessageBox.Close)
            msg.exec_()

        self.MS_ST_search_trainee_override_entry.clear()

    def _clear_search_ms_record_window(self):
        self.MS_ST_search_trainee_textbrowser.clear()

    def _ms_safety_add(self):
        f_name = self.MS_ST_add_student_full_name_entry.text()
        abc = self.MS_ST_add_student_abc_entry.text()
        yoc = self.MS_ST_add_student_yoc_entry.text()
        self.MS_ST_add_student_full_name_entry.setText("First, Last")
        self.MS_ST_add_student_abc_entry.clear()
        self.MS_ST_add_student_yoc_entry.clear()
        query = ("""INSERT INTO staff."SafetyTraining-MS" (first_name, last_name, abc123, year_of_com)
                VALUES (%s, %s, %s, %s);""")

        msg = QMessageBox()
        msg.setWindowTitle("Information")
        detail = ""
        try:
            first, last = f_name.split(",")
            params = [first, last[1:], abc, yoc]

            if abc[:3] != str and int(abc[3:]) > 999:
                detail = "Use abc123 format"
                raise TypeError("Incorrect abc format")
            if int(yoc) != int and int(yoc) < 2000:
                detail = "Years below 2000 are not available"
                raise TypeError("Invalid year")
            insert(query, params)
            msg.setIcon(QMessageBox.Information)
            msg.setText("You have successfully added {}".format(f_name))
            msg.setStandardButtons(QMessageBox.Close)
            msg.exec_()
        except Exception as error:
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error while adding {}".format(f_name))
            msg.setStandardButtons(QMessageBox.Close)
            if "duplicate key" in str(error):
                msg.setDetailedText("User has already been added to the record.")
            elif "not enough values" in str(error):
                msg.setDetailedText("Incorrect form for student's name")
            elif "abc" in str(error):
                msg.setDetailedText(detail)
            elif "year" in str(error):
                msg.setDetailedText(detail)
            elif "invalid literal for int()" in str(error):
                msg.setDetailedText("Check you abc123 and year fields")
            msg.exec_()

    def _ms_safety_search(self):
        first = self.MS_ST_search_trainee_fname_entry.text()
        last = self.MS_ST_search_trainee_lname_entry.text()
        abc = self.MS_ST_search_trainee_abc_entry.text()
        self.MS_ST_search_trainee_fname_entry.clear()
        self.MS_ST_search_trainee_lname_entry.clear()
        self.MS_ST_search_trainee_abc_entry.clear()

        query = ("""SELECT first_name, last_name, abc123, year_of_com, maker, maker_level
                        FROM staff."SafetyTraining-MS"
                        WHERE first_name = %s 
                        OR last_name LIKE %s 
                        OR abc123 LIKE %s;""")

        params = [first, last, abc]

        r = (select(query, params))
        current = "hasn't"
        msg = QMessageBox()
        msg.setWindowTitle("Information")
        detail = ""
        try:
            if int(r[0][3]) > (year() - 2):
                current = 'has'

            page_format = ("""<p><b>Machine Shop - Safety Training Record</b></p><br/>
                                      <p>For: {}</p>
                                      <p>With Student Id: {}</p>
                                      <p>The student {} been safety trained withing the last 2 years</p><br/>
                                      <p>Rowdy Maker: {}</p>
                                      <p>Maker Level: {}</p>
                                      <p>Write OXSDR and click renew to extend this student's
                                      safety training record another year.<p>""".format(r[0][0] + " " + r[0][1],
                                                                                        r[0][2], current,
                                                                                        r[0][4], r[0][5]))
            self.MS_ST_search_trainee_textbrowser.setAcceptRichText(True)
            self.MS_ST_search_trainee_textbrowser.setText(page_format)

        except Exception as error:
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Cannot find user name record")
            msg.setStandardButtons(QMessageBox.Close)
            msg.setDetailedText(str(error))
            msg.exec_()

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
        self.check_last_inv_id.clicked.connect(self.show_last_item_id)
        self.search_file_append_inv.clicked.connect(self.getfile)

    def getfile(self):
        ft = str(self.comboBox_2.currentText())
        file_type = "{} File (*.{})".format(ft, ft.lower())
        manager = OpenFile()
        fname = manager.getfile(file_type)
        if len(fname) > 1:
            h = fname.split("/")
            self.label_55.setText(h[-1])

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

        if not lpi:
            next_id = str(self.inventory_append_cs.currentText()) + inventory_key[1:-1] + "0001"
            self.last_inv_id_label.setText("ID Has Not Been Used")
        elif 0 < lpi < 9:
            next_id = part_id[lpi][0][:-1] + str(int(part_id[lpi][0][-1]) + 1)
        else:
            next_id = "N/A"
        self.label_51.setText(next_id)

    def _set_inventory_overview(self):
        try:
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
        except IndexError:
            pass

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

    def _set_approve_inventory_tab(self):
        def _clear():
            self.approve_text_display.clear()
            Globals.approval_inv_vals = []

        self.refresh_approvals_inventory_button.clicked.connect(self._refresh_inventory_approvals)
        self.approve_table.cellDoubleClicked.connect(self.send_approval2view)
        self.approve_open_button.clicked.connect(self._approval_open_inventory)
        self.approve_confirm_button.clicked.connect(self._commit_approval_inventory)
        self.approve_inventory_clear_button.clicked.connect(_clear)

    def _commit_approval_inventory(self):
        msg = QMessageBox()
        msg.setWindowTitle("Information")

        if self.approve_checkbox_confirm.isChecked():
            print('confirmed')

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
                     """WHERE part_id = %s""".format("public.general_inventory"))

            try:
                insert(query, Globals.approval_inv_vals)

                query = "DELETE FROM private.inventory_update_request WHERE request_id = %s;"
                params = [Globals.inventory_update_req_id]
                # Use insert function for delete
                delete(query, params)

                query = "DELETE FROM private.inventory_approvals WHERE request_id = %s;"
                params = [Globals.inventory_update_req_id]
                # Use insert function for delete
                delete(query, params)

                self.approve_text_display.clear()
                self.approve_checkbox_confirm.setChecked(False)

            except Exception as error:
                detail = "- No request selected.\n" \
                         "- No changes requested.\n" \
                         "- Double click on request_id above to verify entries.\n" + str(error)
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Missing Information")
                msg.setStandardButtons(QMessageBox.Close)
                msg.setDetailedText(detail)
                msg.exec_()

        else:
            detail = "- The action cannot proceed without checking the reviewed checkbutton."
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Incomplete Action")
            msg.setStandardButtons(QMessageBox.Close)
            msg.setDetailedText(detail)
            msg.exec_()

    def _approval_open_inventory(self):
        _ = self.approve_entry_request_id.text()
        query = "SELECT * FROM private.inventory_approvals WHERE request_id = %s;"
        params = [_]
        new = select(query, params)
        new = [item for t in new for item in t]
        try:
            Globals.inventory_update_req_id = new[0]
            query = "SELECT * FROM public.general_inventory WHERE part_id = %s;"
            params = [new[6]]
            Globals.approval_inv_vals = new[6:]
            Globals.approval_inv_vals.append(new[6])
            current = select(query, params)
            current = [item for t in current for item in t]
            table = ""

            query = '''SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s '''
            params = ["general_inventory"]
            cols = select(query, params)
            cols = [item for t in cols for item in t]
            items_changed = []

            nw = new[6:]
            changed = []
            c = current
            for n in c:
                k = c.index(n)
                if n != nw[k]:
                    changed.append(nw[k])
                    changed.append(n)
                    items_changed.append(cols[k])
                c[k] = " "

            for i in range(len(items_changed)):
                table += "<p>Entry {} has changed from {} to {}<p/>".format(items_changed[i],
                                                                            changed[2 * i + 1],
                                                                            changed[2 * i])

            page_format = ("""<body>
                                        <h2><b>Review Request ID for: {}</b></h2>
                                        <h3>Request made on {} by {}</h2>
                                        <p>The item was modified in {} field(s)</p>
                                        <h3><b>Details</b><h3/>
                                        <p>Current Value    New Value<p/>
                                        <p>{}<p/>
                                      </body>""".format(new[7],
                                                        new[1].strftime("%Y-%m-%d"),
                                                        new[2],
                                                        new[3],
                                                        table))

            self.approve_text_display.setText(page_format)
            self.approve_entry_request_id.clear()
        except IndexError:
            pass

    def _refresh_inventory_approvals(self):
        self.approve_table.setRowCount(0)

        query = "SELECT * FROM private.inventory_update_request"
        params = []
        vals = select(query, params)

        self.approve_table.setRowCount(len(vals))

        row = 0
        for entry in vals:
            column = 0
            for v in entry:
                if column == 1:
                    self.approve_table.setItem(row, column, QTableWidgetItem(v.strftime("%Y-%m-%d")))
                else:
                    self.approve_table.setItem(row, column, QTableWidgetItem(str(v)))
                column += 1
            row += 1

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
        else:
            params[15] = False
            nparams[9] = False

        if params[16] == 'False':
            params[16] = False
            nparams[10] = False
        else:
            params[16] = True
            nparams[10] = True

        line_update = 0
        it = 0
        var_changes = []
        for entry in nparams:
            if entry != Globals.inventory_entries_vals[it]:
                var_changes.append((entry, Globals.inventory_entries_vals))
                line_update += 1
            it += 1

        params[3] = line_update

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

    def send_approval2view(self, row, column):
        if column == 0:
            item = self.approve_table.item(row, column)
            self.approve_entry_request_id.setText(item.text())

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
